# Home Drives Remapping in AD
------------

Requirements
------------------
1. CSV file with a list of users. - 'get-aduser -properties mail -filter * |select name,samaccountname,mail |export-csv -path'
2. Update 'PLACEHOLDER\PATH' with the appropriate path to the csv.
3. Update PARENT\DIRECTORY with the share to prepend to the user name. ie - \\server\users\

What it does
------------------
Use a generated list of users to update the homedrive and homedirectory attributes in Active Directory. 