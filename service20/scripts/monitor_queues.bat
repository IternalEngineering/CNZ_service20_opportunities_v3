@echo off
REM Windows batch script to monitor SQS queues

echo ============================================================
echo SQS Queue Monitor for Service20
echo ============================================================
echo.

:menu
echo Select monitoring mode:
echo   1. Monitor once
echo   2. Monitor continuously (5 second refresh)
echo   3. Monitor continuously (30 second refresh)
echo   4. Health check only
echo   5. JSON output
echo   6. Exit
echo.

set /p choice="Enter choice (1-6): "

if "%choice%"=="1" (
    python monitor_queues.py --mode once
    goto end
)

if "%choice%"=="2" (
    python monitor_queues.py --mode continuous --interval 5
    goto end
)

if "%choice%"=="3" (
    python monitor_queues.py --mode continuous --interval 30
    goto end
)

if "%choice%"=="4" (
    python monitor_queues.py --mode health
    goto end
)

if "%choice%"=="5" (
    python monitor_queues.py --mode json
    goto end
)

if "%choice%"=="6" (
    echo Goodbye!
    goto end
)

echo Invalid choice!
echo.
goto menu

:end
pause
