import logging
import os
import sys

dir_name = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(dir_name, "../"))
from descope import (  # noqa: E402
    REFRESH_SESSION_TOKEN_NAME,
    SESSION_TOKEN_NAME,
    AuthException,
    DeliveryMethod,
    DescopeClient,
    common,
)

logging.basicConfig(level=logging.INFO)


def main():
    project_id = ""
    try:
        descope_client = DescopeClient(project_id=project_id)
        logging.info("Going to sign in using OTP...")
        email = input("Please insert email to signin:\n")
        descope_client.otp.sign_up_or_in(method=DeliveryMethod.EMAIL, login_id=email)

        value = input("Please insert the code you received by email:\n")
        try:
            jwt_response = descope_client.otp.verify_code(
                method=DeliveryMethod.EMAIL, login_id=email, code=value
            )
            logging.info("Code is valid")
            session_token = jwt_response[SESSION_TOKEN_NAME].get("jwt")
            refresh_token = jwt_response[REFRESH_SESSION_TOKEN_NAME].get("jwt")

            # Now add phone number
            phone = input("Please insert phone to add to your account:\n")
            descope_client.otp.update_user_phone(
                method=DeliveryMethod.SMS,
                login_id=email,
                phone=phone,
                refresh_token=refresh_token,
            )
            value = input("Please insert the code you received by sms:\n")
            jwt_response = descope_client.otp.verify_code(
                method=DeliveryMethod.SMS, login_id=email, code=value
            )
            logging.info("Code is valid")
            session_token = jwt_response[SESSION_TOKEN_NAME].get("jwt")
            refresh_token = jwt_response[REFRESH_SESSION_TOKEN_NAME].get("jwt")

            # Now start all over again, and do a stepup flow with given email and phone
            descope_client.otp.sign_in(method=DeliveryMethod.EMAIL, login_id=email)
            value = input(
                "Please insert the code you received by email to start stepup flow:\n"
            )
            jwt_response = descope_client.otp.verify_code(
                method=DeliveryMethod.EMAIL, login_id=email, code=value
            )
            logging.info("Initial login is valid, lets continue to the stepup")
            session_token = jwt_response[SESSION_TOKEN_NAME].get("jwt")
            refresh_token = jwt_response[REFRESH_SESSION_TOKEN_NAME].get("jwt")

            descope_client.otp.sign_in(
                method=DeliveryMethod.SMS,
                login_id=email,
                login_options=common.LoginOptions(True, {"k1": "v1"}),
                refresh_token=refresh_token,
            )
            value = input(
                "Please insert the code you received by sms to complete stepup:\n"
            )
            jwt_response = descope_client.otp.verify_code(
                method=DeliveryMethod.SMS, login_id=email, code=value
            )

            logging.info("Code is valid, user properly stepped up")
            session_token = jwt_response[SESSION_TOKEN_NAME].get("jwt")
            refresh_token = jwt_response[REFRESH_SESSION_TOKEN_NAME].get("jwt")

            logging.info(f"jwt_response: {jwt_response}")
        except AuthException as e:
            logging.info(f"Invalid code {e}")
            raise

        try:
            logging.info("going to validate session..")
            descope_client.validate_session(session_token)
            logging.info("Session is valid and all is OK")
        except AuthException as e:
            logging.info(f"Session is not valid {e}")

        try:
            logging.info("refreshing the session token..")
            claims = descope_client.refresh_session(refresh_token)
            logging.info(
                "going to revalidate the session with the newly refreshed token.."
            )

            new_session_token = claims.get(SESSION_TOKEN_NAME).get("jwt")
            descope_client.validate_and_refresh_session(
                new_session_token, refresh_token
            )
            logging.info("Session is valid also for the refreshed token.")
        except AuthException as e:
            logging.info(f"Session is not valid for the refreshed token: {e}")

        try:
            descope_client.logout(refresh_token)
            logging.info("User logged out")
        except AuthException as e:
            logging.info(f"Failed to logged out user, err: {e}")

    except AuthException:
        raise


if __name__ == "__main__":
    main()
