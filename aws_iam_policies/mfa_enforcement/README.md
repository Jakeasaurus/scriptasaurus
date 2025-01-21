# AWS MFA Enforcement Policy

This repository contains an IAM policy that enforces Multi-Factor Authentication (MFA) usage in AWS while allowing users to manage their own MFA devices.

## Purpose

This policy implements a security best practice by:
- Requiring MFA for most AWS actions
- Allowing users to set up and manage their own MFA devices
- Preventing access to AWS resources until MFA is enabled
- Maintaining security while providing necessary permissions for MFA setup

## Policy Overview

The policy consists of five main statements:

1. **AllowViewAccountInfo**: Basic account information access
2. **AllowManageOwnPasswords**: Self-service password management
3. **AllowManageOwnAccessKeys**: Access key management
4. **AllowManageOwnMFA**: MFA device management
5. **DenyAllExceptListedIfNoMFA**: MFA enforcement

## Usage

### Implementation Steps

1. Copy the policy from `mfa_enforcement_policy.json`
2. Create a new IAM policy in your AWS account
3. Attach the policy to:
   - IAM users directly
   - IAM groups (recommended)
   - IAM roles (where applicable)

### User Experience

Users will:
1. Be able to log into the AWS Console
2. Have access to MFA setup tools
3. Be required to configure MFA
4. Have full permitted access only after MFA is enabled

## File Structure

```
.
├── README.md
├── mfa_enforcement_policy.json
└── examples/
```

## Security Considerations

- This policy follows the principle of least privilege
- Users can only manage their own credentials
- MFA setup actions are explicitly allowed without MFA
- All other actions require MFA authentication

## Best Practices

1. Implement this policy alongside other security measures
2. Review and update the policy periodically
3. Monitor MFA adoption through AWS CloudTrail
4. Train users on MFA setup and usage

## Contributing

Feel free to submit issues and enhancement requests!

## License

[MIT License](LICENSE)

## References

- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS MFA Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa.html)
```
