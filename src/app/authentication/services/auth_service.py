import grpc
import jwt
from app.authentication.models import User
from app.generated import auth_pb2, auth_pb2_grpc
from app.otp.services.otp_service import OTPService
from config.settings import SECRET_KEY
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

ROLE_MAP = {
    "investor": auth_pb2.INVESTOR,
    "admin": auth_pb2.ADMIN,
    "startupper": auth_pb2.STARTUPPER,
}

PROTO_ROLE_MAP = {
    auth_pb2.INVESTOR: "investor",
    auth_pb2.ADMIN: "admin",
    auth_pb2.STARTUPPER: "startupper",
}


class AuthService(auth_pb2_grpc.AuthServiceServicer):
    def Register(self, request, context):
        try:
            with transaction.atomic():
                otp_service = OTPService(request.email)
                if otp_service.check_otp():
                    user = User.objects.create_user(
                        email=request.email,
                        password=request.password,
                        first_name=request.first_name,
                        last_name=request.last_name,
                        role=PROTO_ROLE_MAP.get(request.role, "investor"),
                    )
                    # refresh = RefreshToken.for_user(user)
                    return auth_pb2.RegisterResponse(
                        success=True,
                        message="Registration successful",
                        data=auth_pb2.UserData(
                            user_id=str(user.id),
                            email=user.email,
                            first_name=user.first_name,
                            last_name=user.last_name,
                            role=ROLE_MAP.get(user.role, auth_pb2.INVESTOR),
                        ),
                    )
                else:
                    return auth_pb2.RegisterResponse(
                        success=False,
                        message="Invalid OTP",
                    )
        except Exception as e:
            return auth_pb2.RegisterResponse(
                success=False,
                message=str(e),
            )

    def Login(self, request, context):
        try:
            user = User.objects.get(email=request.email)
            if user.check_password(request.password):
                refresh = RefreshToken.for_user(user)
                refresh["role"] = user.role
                refresh["email"] = user.email
                return auth_pb2.LoginResponse(
                    success=True,
                    message="Login successful",
                    data=auth_pb2.LoginData(
                        user_id=str(user.id),
                        first_name=user.first_name,
                        last_name=user.last_name,
                        email=user.email,
                        access_token=str(refresh.access_token),
                        refresh_token=str(refresh),
                    ),
                )
            else:
                return auth_pb2.LoginResponse(
                    success=False,
                    message="Invalid credentials",
                )
        except User.DoesNotExist:
            return auth_pb2.LoginResponse(
                success=False,
                message="User not found",
            )
        except Exception as e:
            return auth_pb2.LoginResponse(
                success=False,
                message=str(e),
            )

    def SendOtp(self, request, context):
        service = OTPService(request.email)
        success = service.send_otp()
        if success:
            return auth_pb2.SendOtpResponse(
                success=True, message="OTP sent successfully"
            )
        else:
            return auth_pb2.SendOtpResponse(success=False, message="Failed to send OTP")

    def VerifyOtp(self, request, context):
        service = OTPService(request.email, request.otp)
        success = service.verify_otp()
        if success:
            return auth_pb2.VerifyOtpResponse(
                success=True, message="OTP verified successfully"
            )
        else:
            return auth_pb2.VerifyOtpResponse(
                success=False, message="Failed to verify OTP"
            )

    def DecodeToken(self, request, context):
        try:
            payload = jwt.decode(request.token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return auth_pb2.DecodeTokenResponse(success=False, message="Token expired")
        except Exception as exc:
            return auth_pb2.DecodeTokenResponse(success=False, message=str(exc))

        user_id = payload.get("user_id") or payload.get("sub") or ""
        return auth_pb2.DecodeTokenResponse(
            success=True,
            message="Token decoded successfully",
            data={
                "user_id": str(user_id),
                "email": payload.get("email", ""),
                "role": payload.get("role", ""),
            },
        )
