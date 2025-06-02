---
title: "Blog Highlight: Active Directory Hardening Blog Series"
date: 2025-02-24T11:30:00-04:00
layout: single
categories:
  - activedirectory
  - security
tags:
  - hardening
  - ldap
  - kerberos
  - smb
  - privilege
description: "A quick spotlight on Jerry Devore’s excellent AD Hardening series, with links to each post and why they matter."
share: true
related: true
last_modified_at: 2025-06-01T23:00:00-04:00
---


[Jerry Devore](https://techcommunity.microsoft.com/users/jerrydevore/199458), a Senior Premier Field Engineer at Microsoft (at the time of this post), has created an absolute must-read blog series on Active Directory Hardening. Even if AD hardening isn’t your primary focus, this is one of the most comprehensive collections of AD knowledge I’ve come across. If you manage Active Directory, you need to understand the concepts he covers.

[Active Directory Hardening Series - Part 1 – Disabling NTLMv1](https://techcommunity.microsoft.com/blog/coreinfrastructureandsecurityblog/active-directory-hardening-series---part-1-%E2%80%93-disabling-ntlmv1/3934787)

NTLMv1, an outdated authentication protocol, is vulnerable to various attacks. Transitioning to NTLMv2 enhances security by providing stronger encryption and better resistance to attacks.

[Active Directory Hardening Series - Part 2 – Removing SMBv1](https://techcommunity.microsoft.com/blog/coreinfrastructureandsecurityblog/active-directory-hardening-series---part-2-%E2%80%93-removing-smbv1/3988317)

SMBv1, introduced decades ago, lacks modern security features and is susceptible to multiple vulnerabilities. Eliminating SMBv1 reduces the attack surface. This process includes auditing current SMB usage, identifying dependencies, and systematically disabling SMBv1 on all systems.

[Active Directory Hardening Series - Part 3 – Enforcing LDAP Signing](https://techcommunity.microsoft.com/blog/coreinfrastructureandsecurityblog/active-directory-hardening-series---part-3-%E2%80%93-enforcing-ldap-signing/4066233)

LDAP traffic, if unsigned, can be intercepted or tampered with, posing significant security risks. Enforcing LDAP signing ensures the integrity and authenticity of LDAP communications. This measure involves configuring domain controllers to require LDAP signing and ensuring all client applications support and implement LDAP signing.

[Active Directory Hardening Series - Part 4 – Enforcing AES for Kerberos](https://techcommunity.microsoft.com/blog/coreinfrastructureandsecurityblog/active-directory-hardening-series---part-4-%E2%80%93-enforcing-aes-for-kerberos/4114965)

Kerberos, a cornerstone of AD authentication, traditionally used the RC4 encryption algorithm, which is now considered weak. Enforcing AES encryption for Kerberos tickets enhances security by utilizing stronger cryptographic methods. This transition requires updating account encryption settings and ensuring all systems and applications support AES.

[Active Directory Hardening Series - Part 5 – Enforcing LDAP Channel Binding](https://techcommunity.microsoft.com/blog/coreinfrastructureandsecurityblog/active-directory-hardening-series---part-5-%E2%80%93-enforcing-ldap-channel-binding/4235497)

LDAP channel binding adds an extra layer of security by binding the TLS tunnel to the LDAP session, mitigating man-in-the-middle attacks. Implementing this involves configuring domain controllers to require channel binding tokens and updating clients to support this feature.

[Active Directory Hardening Series - Part 6 – Enforcing SMB Signing](https://techcommunity.microsoft.com/blog/coreinfrastructureandsecurityblog/active-directory-hardening-series---part-6-%E2%80%93-enforcing-smb-signing/4272168)

SMB signing ensures that SMB communications are authenticated and that their integrity is verified, protecting against tampering and certain types of relay attacks. Enforcing SMB signing involves configuring both clients and servers to require signed SMB communications.

[Active Directory Hardening Series - Part 7 – Implementing Least Privilege](https://techcommunity.microsoft.com/blog/coreinfrastructureandsecurityblog/active-directory-hardening-series---part-7-%E2%80%93-implementing-least-privilege/4366626)

Adopting the principle of least privilege involves granting users and services only the permissions necessary to perform their tasks, minimizing potential attack vectors. This practice includes regular audits of user permissions, reducing the number of privileged accounts, and implementing role-based access controls.