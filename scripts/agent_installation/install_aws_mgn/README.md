# Script README

This script creates a directory named `aws-mgn-agent` in the `C:\` drive and downloads the AWS Migration Hub replication agent installer for Windows. It then installs the agent using the provided AWS access key, secret access key, and region.

## Prerequisites

- This script requires PowerShell to be installed on the system.
- Ensure that you have valid AWS access key ID, secret access key, and the desired region for the migration.

## Usage

1. Open a PowerShell session or a PowerShell script editor.
2. Copy and paste the script into the session or editor.
3. Replace the placeholders `YOUR-REGION-HERE`, `YOUR-ACCESS-KEY-HERE`, and `YOUR-SECRET-KEY-HERE` with your AWS region, access key ID, and secret access key, respectively.
4. Run the script.

**Note:** Make sure you have appropriate permissions and that the access key provided has sufficient privileges to install the agent.

## Script Steps

1. The script creates a directory named `aws-mgn-agent` in the `C:\` drive using the `New-Item` cmdlet.
2. It assigns the URL of the AWS Migration Hub replication agent installer to the `$url` variable.
3. The script sets the output path for the installer to `C:\aws-mgn-agent\AwsReplicationWindowsInstaller.exe` by assigning it to the `$outpath` variable.
4. It uses the `Invoke-WebRequest` cmdlet to download the installer from the provided URL and save it to the output path.
5. The script waits for 10 seconds using the `Start-Sleep` cmdlet. You can modify this value if needed.
6. Finally, it runs the `AwsReplicationWindowsInstaller.exe` with the appropriate parameters to install the agent. Make sure to replace `YOUR-REGION-HERE`, `YOUR-ACCESS-KEY-HERE`, and `YOUR-SECRET-KEY-HERE` with the actual values.

## Disclaimer

Please note that this script is provided as-is and OpenAI takes no responsibility for any issues or damages that may arise from its use. Ensure that you have tested the script in a controlled environment before deploying it to a production system.
