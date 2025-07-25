"""
Async check runner and state management for PageCheck.
"""
from compatibility_checks import CheckType
from async_operations import AsyncOperations as AO, Status
import tempfile
import pathlib
import pickle
from services.system import get_admin

def run_checks(checks, done_checks, active_check, update_callback, check_wrapper_callback, monitor_callback, logger):
    check_types = list(CheckType)
    logger.info(f"Total checks to run: {len(check_types)}, Current active check: {active_check}")
    if active_check < len(check_types):
        check_type = check_types[active_check]
        logger.info(f"Running check {active_check + 1}/{len(check_types)}: {check_type}")
        check_function = checks.check_functions[check_type]
        logger.info(f"Got check function for {check_type}: {check_function}")
        check_operation = AO()
        logger.info(f"Created async operation for {check_type}")
        check_operation.run_async_process(
            check_wrapper_callback, args=(check_type, check_function, check_operation)
        )
        logger.info(f"Started async process for {check_type}")
        monitor_callback(
            check_operation,
            lambda: run_checks(checks, done_checks, active_check + 1, update_callback, check_wrapper_callback, monitor_callback, logger),
        )
        logger.info(f"Monitoring async operation for {check_type}")
    else:
        logger.info("All checks completed.")
        update_callback()

def check_wrapper(check_type, check_function, operation, done_checks, LN, app_config, logger, update_job_var_and_progressbar):
    logger.info(f"Starting check_wrapper for {check_type}")
    if done_checks.checks[check_type].returncode is None:
        logger.info(f"Running check for {check_type}")
        update_job_var_and_progressbar(check_type)
        try:
            logger.info(f"Calling check function for {check_type}")
            result = check_function()
            logger.info(f"Check ({check_type}): {result.result}, Return code: {result.returncode}")
            if result.returncode == -200:
                logger.warning(f"Check {check_type} requires admin privileges")
                with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as temp_file:
                    pickle.dump(done_checks, temp_file)
                    temp_file_path = pathlib.Path(temp_file.name).absolute()
                args_string = f'--checks_dumb "{temp_file_path}"'
                operation.status = Status.FAILED
                get_admin(args_string)
            else:
                logger.info(f"Check {check_type} completed successfully")
                done_checks.checks[check_type] = result
        except Exception as e:
            logger.error(f"Error during check {check_type}: {e}")
            raise
    else:
        logger.info(f"Check {check_type} already completed, skipping")
