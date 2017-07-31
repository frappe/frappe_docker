# Start ChromeDriver and make it non-blocking with ampersand
./bin/chromedriver &

# Keep track of the ChromeDrivers Process ID
TASK_PID=$!

# Wait for 10 seconds to give the ChromeDriver a chance to fail if there is an
# issue.
sleep 10

# ps -p Checks if the process is still running. If it is it returns 0,
# otherwise it returns 1
ps -p $TASK_PID > /dev/null
TASK_RUNNING=$?

# Check if the process is still running by examining the exit code of ps -p
TEST_RESULT=1
if [ $TASK_RUNNING -eq 0 ]; then
  # Still running so return with safe exit code
  TEST_RESULT=0
fi

kill $TASK_PID

exit $TEST_RESULT
