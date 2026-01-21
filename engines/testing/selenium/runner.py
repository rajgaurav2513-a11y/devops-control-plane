from core.models.result import ExecutionResult, Status


def run_ui_tests(cfg: dict) -> ExecutionResult:
    """
    UI (Selenium) Test Runner – FINAL

    - Selenium is OPTIONAL
    - No hard dependency on browser / driver
    - Fails gracefully
    - Platform-safe
    """

    # -----------------------------
    # Lazy import (MANDATORY)
    # -----------------------------
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        return ExecutionResult(
            stage="TEST",
            status=Status.SKIPPED,
            message="Selenium not installed",
            action="Install selenium to enable UI tests",
        )

    logs = []

    # -----------------------------
    # Driver setup (SAFE)
    # -----------------------------
    driver = None
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
    except Exception as e:
        return ExecutionResult(
            stage="TEST",
            status=Status.SKIPPED,
            message="Unable to start browser for UI tests",
            logs=[str(e)],
            action="Ensure Chrome & driver are available or disable UI tests",
        )

    # -----------------------------
    # Execute UI steps
    # -----------------------------
    try:
        target = cfg.get("target")
        if not target:
            return ExecutionResult(
                stage="TEST",
                status=Status.BLOCKED,
                message="UI test target URL not provided",
            )

        for step in cfg.get("ui", []):

            if "open" in step:
                url = target.rstrip("/") + step["open"]
                driver.get(url)
                logs.append(f"OPEN {url}")

            if "click" in step:
                driver.find_element(By.CSS_SELECTOR, step["click"]).click()
                logs.append(f"CLICK {step['click']}")

            if "expect_text" in step:
                body = driver.find_element(By.TAG_NAME, "body").text
                expected = step["expect_text"]
                if expected not in body:
                    return ExecutionResult(
                        stage="TEST",
                        status=Status.FAILED,
                        message="UI assertion failed",
                        logs=logs + [f"Expected text not found: {expected}"],
                    )

        return ExecutionResult(
            stage="TEST",
            status=Status.SUCCESS,
            message="UI tests passed",
            logs=logs,
        )

    finally:
        # -----------------------------
        # Cleanup (MUST NOT FAIL)
        # -----------------------------
        try:
            if driver:
                driver.quit()
        except Exception:
            pass
