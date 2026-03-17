import grpc
import jwt
from app.authentication.models import User
from app.generated import auth_pb2, auth_pb2_grpc
from app.otp.services.otp_service import OTPService
from config.settings import SECRET_KEY
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken


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
                        role=request.role,
                    )
                    # refresh = RefreshToken.for_user(user)
                    return auth_pb2.RegisterResponse(
                        success=True,
                        message="Registration successful",
                        data=auth_pb2.UserData(
                            user_id=user.id,
                            email=user.email,
                            first_name=user.first_name,
                            last_name=user.last_name,
                            role=user.role,
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
                return auth_pb2.LoginResponse(
                    success=True,
                    message="Login successful",
                    data=auth_pb2.LoginData(
                        user_id=user.id,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        email=user.email,
                        role=user.role,
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

    def SendOTP(self, request, context):
        service = OTPService(request.email)
        success = service.send_otp()
        if success:
            return auth_pb2.SendOTPResponse(
                success=True, message="OTP sent successfully"
            )
        else:
            return auth_pb2.SendOTPResponse(success=False, message="Failed to send OTP")

    def VerifyOTP(self, request, context):
        service = OTPService(request.email, request.otp)
        success = service.verify_otp()
        if success:
            return auth_pb2.VerifyOTPResponse(
                success=True, message="OTP verified successfully"
            )
        else:
            return auth_pb2.VerifyOTPResponse(
                success=False, message="Failed to verify OTP"
            )

    def DecodeToken(self, request, context):
        try:
            payload = jwt.decode(request.token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return auth_pb2.DecodeTokenResponse()

        return auth_pb2.DecodeTokenResponse(
            user_id=str(payload["user_id"]),
            email=payload.get("email", ""),
            role=payload.get("role", ""),
        )
