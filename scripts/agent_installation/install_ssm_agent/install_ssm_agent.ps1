# Define the name of the software to search for.  This can just be a keyword if you don't want to use the whole name

$software = “SSM”



# This will check to see if that keyword exists in the Uninstall list and return "True/False" as a variable

$installed = ((gp HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*).DisplayName -Match $software).Length -gt 0



# This will check the condition of the variable

If(-Not $installed) {

    

    # This will download the file from the internet

        $progressPreference = 'silentlyContinue'

    Invoke-WebRequest -Uri "https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/windows_amd64/AmazonSSMAgentSetup.exe" -OutFile "$env:USERPROFILE\Desktop\SSMAgent_latest.exe"



    # Assuming your file is an .exe file, this will execute the file

     Start-Process `

    -FilePath $env:USERPROFILE\Desktop\SSMAgent_latest.exe `

    -ArgumentList "/S"



     # This will remove the SSM Agent Setup executable

      rm -Force $env:USERPROFILE\Desktop\SSMAgent_latest.exe



     # This will restart the agent

     Restart-Service AmazonSSMAgent

}



else {



    # Tell the user if the program (or similar program) is already installed

    Write-Host "A program with the keyword '$software' already exists."

}



# End the script

Write-Host "Done!"