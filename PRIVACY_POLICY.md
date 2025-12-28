# Privacy Policy

**Effective Date:** December 28, 2025
**Last Updated:** December 28, 2025

This Privacy Policy describes how the Expedition Narrator GPT ("the GPT", "we", "our") handles information when you use our Custom GPT for Aeon's End expedition narration.

## 1. Overview

Expedition Narrator is a Custom GPT that provides interactive narrative experiences for the board game Aeon's End. It generates randomized expedition packets and delivers atmospheric storytelling based on your gameplay choices.

## 2. Information We Collect

### 2.1 User-Provided Input

When using the GPT, you may provide the following information:

- **Mage count** – the number of player characters (required)
- **Expedition preferences** – length (short/standard/long), content scope (game expansions/waves)
- **Random seed** – an optional integer for reproducible expeditions
- **Game outcomes** – win/lose results and optional narrative details after each battle

**We do not collect or request:**
- Personal names or identities
- Email addresses or contact information
- Payment or financial information
- Location data
- Any other personally identifiable information (PII)

### 2.2 Server Logs

Our backend API endpoint (`skriptguruai.site`) may automatically log standard HTTP request information, including:

- Timestamp of the request
- IP address
- Request parameters (mage count, length, content scope, seed)
- HTTP headers

These logs are used solely for debugging, security monitoring, and service maintenance. They are not used for tracking, profiling, or marketing purposes.

## 3. How We Use Information

The information you provide is used exclusively to:

- Generate expedition packets containing game content (mages, nemeses, friends, foes, settings)
- Deliver narrative responses based on your gameplay choices
- Ensure collision-free selection (no duplicate game elements)

**We do not:**
- Store conversation history on our servers
- Create user accounts or profiles
- Share data with third parties for marketing
- Use data for training AI models

## 4. Data Retention

### 4.1 Stateless Processing

Each API request is processed independently and statelessly. The backend selector does not maintain:

- Session data between requests
- User accounts or persistent profiles
- Conversation history

### 4.2 Server Logs

Standard HTTP server logs may be retained for a limited period for operational purposes, after which they are automatically deleted.

## 5. Third-Party Services

### 5.1 OpenAI ChatGPT Platform

The Expedition Narrator GPT operates within OpenAI's ChatGPT platform. Your interactions with the GPT are subject to [OpenAI's Privacy Policy](https://openai.com/policies/privacy-policy) and [Terms of Use](https://openai.com/policies/terms-of-use).

OpenAI may collect and process data according to their own policies, including:

- Conversation content
- Usage data
- Account information (if applicable)

We encourage you to review OpenAI's policies for complete information about how your data is handled on their platform.

### 5.2 No Other Third-Party Sharing

Beyond the OpenAI platform integration, we do not share, sell, or transfer your data to any other third parties.

## 6. Data Security

We implement reasonable security measures to protect the information processed through our service:

- HTTPS encryption for all API communications
- No storage of sensitive personal information
- Limited data retention for server logs

## 7. Children's Privacy

The Expedition Narrator GPT is designed for general audiences interested in the Aeon's End board game. We do not knowingly collect personal information from children under 13 years of age. If you believe a child has provided personal information, please contact us so we can take appropriate action.

## 8. Your Rights

Depending on your jurisdiction, you may have certain rights regarding your data, including:

- **Access** – Request information about data we may have collected
- **Deletion** – Request deletion of any data associated with you
- **Correction** – Request correction of inaccurate data

Since we do not collect or store personal data, these rights primarily apply to any server logs that may contain your IP address. To exercise these rights, please contact us using the information below.

## 9. Changes to This Policy

We may update this Privacy Policy from time to time. Changes will be indicated by updating the "Last Updated" date at the top of this document. Continued use of the GPT after changes constitutes acceptance of the updated policy.

## 10. Open Source

The Expedition Narrator project is open source software licensed under the MIT License. The source code is available for review, which allows you to verify our data handling practices.

## 11. Contact Us

If you have questions, concerns, or requests regarding this Privacy Policy or our data practices, please:

- Open an issue on our GitHub repository
- Contact the project maintainer through the repository

---

*This Privacy Policy applies only to the Expedition Narrator GPT and its associated backend services. It does not cover third-party websites, services, or the OpenAI ChatGPT platform itself.*
