from .auth_controller import AuthToken, run_auth_all_test
from .content_controller import run_content_all_test
from .folder_controller import run_folder_all_test
from .user_controller import run_user_all_test


def run_apis_all_test():
    run_auth_all_test()
    run_content_all_test()
    run_folder_all_test()
    run_user_all_test()
