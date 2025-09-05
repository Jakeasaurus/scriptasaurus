$domain_controller = YOUR-DOMAIN-CONTROLLER
$username = DOMAIN\USERNAME
Reset-ComputerMachinePassword -Server $domain_controller -Credential $username

#You will be prompted to enter password