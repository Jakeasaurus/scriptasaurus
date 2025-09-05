###Update DNS Records with PowerShell
This PowerShell script allows you to easily update DNS records.

##Prerequisites
-PowerShell
-Access to a DNS server
##Usage
-Update the $dnsServer variable with the IP address of your DNS server.
-Update the $dnsRecord variable with the DNS record you want to update.
-Update the $newIP variable with the new IP address for the DNS record.
-Update the $dnsRecordType variable with the DNS record type (A, AAAA, CNAME, etc.).
-Run the script with PowerShell.

##Example
`PS C:\> .\update-dns.ps1
DNS record updated successfully`

In this example, the script is run with the default settings, updating the DNS record for www.example.com with the new IP address 203.0.113.5. The script successfully updates the DNS record, and outputs a success message.