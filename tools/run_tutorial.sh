#!/bin/bash

try=0
while [ $try -lt $num_tries ]; do 
    echo " "
    echo "Running the tutorial mission in ${TOMCAT}."
    echo " "

    ${TOMCAT}/build/bin/runExperiment --mission 0 \
      --record_path=tutorial_saved_data.tgz \
      >& ${tutorial_mission_log} &
    bg_pid=$!
    echo "Running: ${TOMCAT}/build/bin/runExperiment --mission 0"
    echo "Process is $bg_pid - waiting for it"
    wait $bg_pid
    tutorial_mission_status=$?

    if [[ ${tutorial_mission_status} -eq 0 ]]; then
        tutorial_mission_status=`grep -c 'Error starting mission' ${tutorial_mission_log}`
    fi


    if [[ ${tutorial_mission_status} -eq 0 ]]; then
        echo "Tutorial mission ended with success status."
        echo " "
        break
    fi 

    let try+=1 

    if [[ $try -lt $num_tries ]]; then 
        echo "Tutorial mission ended with failure status."
        echo "Killing all Minecraft and Malmo processes that can be found and trying again."
        ${TOMCAT}/tools/kill_minecraft.sh
        ${TOMCAT}/tools/check_minecraft.sh
    fi 
done
rm tutorial_saved_data.tgz
exit 0