

# **Architecting an Isolated, Ephemeral AI Trading Agent for Cryptocurrency Exchanges**

## **Executive Summary**

This report provides a comprehensive architectural blueprint for deploying an ephemeral, AI-driven trading agent with a core focus on security, budget isolation, and operational autonomy. The primary objective is to create a system where an experimental trading bot can operate with a strictly defined, hard-enforced capital limit without exposing the user's main portfolio to risk.

The analysis concludes that the preferred exchange, **Bitvavo, is fundamentally unsuitable for this use case**. Its account model, which lacks sub-accounts or any form of balance-scoped API keys, makes true budget isolation impossible. Any API key generated on a Bitvavo account has implicit access to the entire account's capital, rendering software-based budget limits insecure. This structural limitation is compounded by a critical security vulnerability: withdrawals initiated via Bitvavo's API explicitly bypass Two-Factor Authentication (2FA) and email confirmations. This design choice elevates the risk of a compromised API key from a limited threat to a potentially catastrophic event for the entire account.

Consequently, the recommended architecture mandates the use of an exchange with native **sub-account functionality**. Platforms such as **Binance, Kraken, and Bybit** offer robust solutions, allowing for the creation of segregated trading environments. Each sub-account can be funded with a precise budget and assigned its own dedicated API key, which is strictly limited to that sub-account's balances and permissions. This exchange-enforced segregation provides the necessary hard boundary for risk management.

The proposed implementation involves a trading agent built on a mature Python framework like **Freqtrade**, running inside a hardened, ephemeral **Docker container**. The agent's lifecycle is automated, with the container being created for a fixed duration and automatically destroyed upon completion. API keys and other secrets must be managed through a secure system like Docker Secrets or HashiCorp Vault, never hard-coded or passed as simple environment variables.

A significant non-technical risk identified is the potential for the user's activities to be reclassified by the Dutch tax authorities (Belastingdienst) from passive investing (taxed under "Box 3") to professional trading (taxed under "Box 1"). The use of a semi-autonomous, high-frequency AI agent strongly points towards professional activity, which would subject all trading profits to significantly higher income tax rates, fundamentally altering the financial viability of the project.

The final blueprint outlines a secure, multi-layered system where an LLM acts as a strategy *orchestrator* through function calling, while deterministic, auditable code handles all execution and risk management. This includes modules for Value-at-Risk (VaR) monitoring and drawdown-based kill-switches, ensuring the AI's suggestions are always subject to strict, predefined safety protocols.

## **Part I: Exchange Platform Analysis for Isolated Operations**

The viability of an isolated trading agent is contingent upon the capabilities of the underlying exchange platform. This section analyzes the account models and API functionalities of Bitvavo and leading alternatives to determine their suitability for creating a secure, ring-fenced trading environment.

### **A. Bitvavo Account Model & API Capabilities**

A thorough review of Bitvavo's platform policies and technical documentation reveals critical limitations that prevent the secure implementation of an isolated trading agent.

#### **1\. Sub-accounts and Wallet Partitions**

The most significant constraint of the Bitvavo platform is its lack of support for sub-accounts or any other mechanism for partitioning funds within a single user profile. Official support documentation states unequivocally, "It is currently not possible to create subaccounts within your existing Bitvavo account".1 This is a foundational architectural deficiency for the proposed use case. Without exchange-level segregation, any trading activity initiated via an API key inherently operates against the total capital pool of the main account. This single design choice makes it impossible to establish a hard, reliable budget limit for an automated agent, directly violating the project's primary isolation requirement.

#### **2\. API Key Granularity and Security Features**

Bitvavo's API provides a set of permissions that, while functional for general trading, lack the fine-grained control needed for secure, isolated automation.3

* **Key Permissions:** The API supports three primary permission levels: "Read-only," "Trade digital assets," and "Withdraw digital assets".3 It is possible to create a key that can trade but not withdraw by granting only the first two permissions. This is a standard and necessary security feature.  
* **Balance Scoping:** A critical missing feature is the ability to scope an API key to a specific subset of the account's balance. An API key with "Read-only" permissions can view the entirety of the account's holdings across all assets.3 This prevents the creation of a "least privilege" key that is blind to the user's main portfolio, failing a key tenet of secure system design.  
* **IP Whitelisting:** The platform supports and strongly recommends IP whitelisting for API keys.6 This is an essential security control that restricts API access to pre-approved IP addresses, significantly reducing the attack surface.

A severe and explicitly documented risk is that **withdrawals initiated via the API bypass the standard 2FA and email confirmation security loops**.3 The official API documentation for the

/v2/withdrawal endpoint warns, "2FA and address confirmation by email are disabled for withdrawals using the API".7 The lack of sub-accounts dramatically amplifies the severity of this feature. On an exchange with sub-accounts, a compromised withdrawal key would only expose the funds within that specific sub-account. On Bitvavo's monolithic account structure, a compromised API key with withdrawal permissions becomes a single point of failure for the

*entire account*, allowing an attacker to drain all funds without triggering the user's primary security alerts (2FA prompts or email confirmations). This makes granting withdrawal permissions to any automated system on Bitvavo an unacceptable risk.

#### **3\. Legal & Terms of Service (ToS) Limits**

Bitvavo's Terms of Service present a clear legal barrier to a common workaround for the lack of sub-accounts. Article 2.7 of the user agreement explicitly states, "User may create and use only one Account" for personal use.8 The platform's systems are designed to enforce this rule, automatically blocking any subsequent accounts created by the same individual.1 This policy eliminates the possibility of creating a separate, secondary personal account to isolate the trading bot's funds. While opening a corporate account is an option, it involves a different and more complex KYC/onboarding process and does not resolve the underlying architectural issues for ephemeral, multi-bot strategies.1

### **B. Budget Ring-Fencing Options & Exchange Alternatives**

Given Bitvavo's limitations, achieving true budget isolation requires exploring alternative architectures and platforms.

#### **1\. Software Guard-rails**

This approach involves implementing budget limits entirely within the trading bot's application logic. The bot would track its own capital usage and be programmed to not exceed a max\_exposure variable. Trading frameworks like Freqtrade offer "protections" such as MaxDrawdown, which can halt trading after a certain loss threshold is reached.10 However, this method offers no genuine security. It relies on the flawless execution of the bot's code. A software bug, a dependency vulnerability, or a logic error could easily cause the bot to ignore these internal limits. Since the underlying API key still has access to the full account balance, this method fails to protect against the primary threat model of a compromised or malfunctioning agent.

#### **2\. On-Chain Segregation**

A more secure, albeit operationally cumbersome, method involves using an external, on-chain wallet (e.g., a hardware wallet) for capital segregation. The workflow would be:

1. Transfer a fixed budget from the private wallet to the Bitvavo account.11  
2. Run the bot using a trade-only API key.  
3. Upon completion, withdraw all funds from Bitvavo back to a whitelisted address in the private wallet.12

This architecture protects the main capital held off-exchange but introduces significant friction and new risks. Each bot run incurs at least two on-chain transactions, with associated network fees and confirmation delays, making it ill-suited for high-frequency or short-lived agents. Furthermore, if the final withdrawal step is automated to maintain autonomy, it requires an API key with withdrawal permissions, re-introducing the catastrophic 2FA bypass risk.7 If the withdrawal is manual, it defeats the purpose of a fully automated system.

#### **3\. Alternative Exchanges with Native Sub-Accounts**

The most robust, secure, and efficient solution is to use an exchange that is architecturally designed for this purpose. Binance, Kraken, and Bybit are leading examples that provide native sub-account functionality, offering true, exchange-enforced isolation.

| Feature | Bitvavo | Binance | Kraken | Bybit |
| :---- | :---- | :---- | :---- | :---- |
| **Sub-Account Support** | No 1 | Yes 13 | Yes 14 | Yes 15 |
| **API Sub-Account Creation** | N/A | Yes 16 | Yes 17 | Yes (UI/API) 18 |
| **API Keys per Sub-Account** | No (Account-wide) | Yes 19 | Yes 14 | Yes 20 |
| **Balance Scoping for Keys** | No | Yes (Implicit) 19 | Yes (Implicit) 14 | Yes (Implicit) 18 |
| **Internal Asset Transfers** | N/A | Yes (Fee-free) 13 | Yes 21 | Yes (Fee-free) 15 |
| **IP Whitelisting** | Yes 6 | Yes 22 | Yes | Yes 18 |

* **Binance:** Offers a mature and well-documented API for creating and managing sub-accounts programmatically.16 API keys can be generated specifically for a sub-account, inheriting its segregated balance and permissions, providing the required isolation.19 Fee-free internal transfers make budget management seamless.13  
* **Kraken:** Also provides strong sub-account support with separate API key management and margining at the sub-account level.14 The API allows for programmatic creation of sub-accounts and internal fund transfers.17 The setup process may be slightly more involved, potentially requiring separate verification steps for sub-accounts.14  
* **Bybit:** Supports up to 20 "Standard Subaccounts" per main account, which can be managed via API.15 It allows for the creation of sub-account-specific API keys and fee-free internal transfers, meeting the core requirements.15

**Conclusion:** Exchanges with native sub-account capabilities are the only viable option for securely implementing the proposed trading agent. They provide the hard-enforced segregation that Bitvavo lacks, making them the superior choice for this architecture.

## **Part II: Architectural Framework for the Trading Agent**

This section outlines the technical design of the ephemeral trading agent, assuming the use of an exchange that supports sub-accounts. The focus is on containerization, security, and the integration of the trading and intelligence layers.

### **C. Container & Secret Management**

The operational security of the agent depends on a well-architected container environment with robust secret management and lifecycle controls.

#### **1\. Best Practice for Passing API Keys**

Storing API keys securely is paramount. The following methods are evaluated from least to most secure:

* **Anti-Pattern (Environment Variables):** Passing secrets as standard Docker environment variables is highly discouraged. These variables can be easily inspected by anyone with access to the Docker host (docker inspect) and can leak through logs or linked containers.23 This method offers minimal security.  
* **Docker Secrets:** This is the standard Docker-native approach for managing secrets within a Docker Swarm environment. Secrets are encrypted both at rest within the Swarm's Raft database and in transit to the container. They are mounted as in-memory files (at /run/secrets/\<secret\_name\>) and are only accessible to services that have been explicitly granted permission.24 This is a secure and practical solution for a single-node or multi-node Swarm deployment.  
* **Kubernetes Secrets:** In a Kubernetes environment, secrets are the native management object. However, by default, they are only Base64 encoded, not encrypted, within the etcd data store.27 Administrators must explicitly configure encryption-at-rest to secure them properly. This is the standard for Kubernetes but is overly complex for a non-Kubernetes deployment.  
* **HashiCorp Vault:** Vault is a dedicated, external secrets management platform that represents the gold standard. It provides advanced capabilities such as dynamic secret generation, automated key rotation, fine-grained access policies, and detailed audit logs.28 Integration with Docker can be achieved via a sidecar container or the Vault Secrets Operator, which syncs Vault secrets into native Kubernetes secrets.30

For the specified use case, **Docker Secrets** offers the best balance of robust security and implementation simplicity. If the project scales to a more complex, production-grade infrastructure, migrating to **HashiCorp Vault** would be the recommended path.

#### **2\. Time-to-Live (TTL) Enforcement**

The container's ephemeral nature must be reliably enforced.

* **Primary Mechanism (--rm flag):** The most straightforward method is to launch the container with the docker run \--rm flag. This flag instructs the Docker daemon to automatically remove the container and its filesystem as soon as its main process exits.31 The container's entrypoint script would be responsible for running the trading bot within a timeout wrapper (e.g., the  
  timeout command in Linux or an internal Python timer), ensuring the process exits after the designated TTL.  
* **Secondary Mechanism (External Cron Killer):** As a fail-safe, a host-level cron job can be configured to periodically clean up any containers that may have failed to exit properly. A script running docker stop \<container\_name\> && docker rm \<container\_name\> or a more general docker container prune with a time filter (e.g., \--filter "until=8h") can ensure no agent overstays its intended lifespan.33

The combination of an internal timeout within the container's main process and the \--rm flag provides a self-contained and reliable lifecycle. The external cron job serves as a robust secondary cleanup mechanism.

#### **3\. Network Firewall Rules**

To prevent data exfiltration and limit the container's attack surface, its network access must be strictly curtailed. The goal is to allow outbound connections only to the exchange's API endpoints.

* **Implementation with iptables:** On a Linux host, this can be achieved by manipulating Docker's iptables chains. The DOCKER-USER chain is specifically designed for custom user rules and is evaluated before Docker's default rules, making it the ideal place for these restrictions.35  
* **Blueprint:**  
  1. **Create a dedicated network:** Isolate the bot on a custom bridge network: docker network create \--internal bot-net-isolated. The \--internal flag prevents any external connectivity by default.37 To allow specific outbound traffic, a more granular approach is needed. A standard bridge network is better:  
     docker network create bot-net.  
  2. **Identify Exchange IPs:** Obtain the static IP addresses for the chosen exchange's API endpoints. This is a critical prerequisite.  
  3. **Configure iptables:** Add rules to the DOCKER-USER chain to whitelist traffic. Let's assume the bot-net subnet is 172.18.0.0/16 and the exchange API is at 1.2.3.4.  
     Bash  
     \# Get the bot-net interface name (e.g., br-xxxxxxxx)  
     IFACE=$(docker network inspect bot-net | jq \-r '..Id' | sed 's/^\\(..........\\).\*/br-\\1/')

     \# Allow outbound traffic to the exchange API on HTTPS  
     iptables \-I DOCKER-USER \-o $IFACE \-d 1.2.3.4 \-p tcp \--dport 443 \-j ACCEPT

     \# (Optional) Allow outbound DNS if needed  
     \# iptables \-I DOCKER-USER \-o $IFACE \-d 8.8.8.8 \-p udp \--dport 53 \-j ACCEPT

     \# Drop all other outbound traffic from this network  
     iptables \-A DOCKER-USER \-o $IFACE \-j DROP

* **The DNS Challenge:** A strict IP-only firewall will block DNS resolution. The most secure pattern is to resolve the API endpoint's IP address *outside* the container and pass it in as configuration, allowing the container to operate without DNS access. An alternative is to whitelist access to a trusted DNS server (e.g., 8.8.8.8), but this slightly widens the network perimeter.

### **D. Trading Framework & LLM Orchestration**

The agent's intelligence is composed of a deterministic trading framework augmented by an LLM-based orchestration layer and supported by robust risk and forecasting modules.

#### **1\. Trading Engine Selection**

* **Freqtrade:** A highly mature, open-source Python framework built on the CCXT library, giving it broad exchange support.38 Its key advantages are its comprehensive, pre-built modules for backtesting, hyper-optimization, money management, and, crucially, risk management "Protections" like  
  StoplossGuard and MaxDrawdown.10 This allows developers to focus on strategy logic rather than foundational infrastructure.  
* **Jesse:** A strong alternative that prioritizes simplicity and backtesting accuracy.41 It also provides a complete framework with risk management tools and live trading capabilities.43 It operates on a freemium model, with advanced features requiring a license.44  
* **Custom CCXT Loop:** This approach involves building the entire trading bot from the ground up using the ccxt library.45 While offering maximum flexibility, it requires a massive engineering effort to replicate the features (state management, risk controls, backtesting, reporting) that frameworks like Freqtrade provide out of the box.

For this project, **Freqtrade** is the recommended engine. Its extensive and battle-tested feature set, particularly its modular risk protections, provides a solid and secure foundation upon which to build the more experimental AI components.

#### **2\. LLM Integration via Function Calling**

The integration of a Large Language Model (LLM) must be done in a way that preserves security and determinism. The LLM should not execute trades directly but rather suggest actions in a structured format.

* **Architecture:** The "function calling" or "tool use" capability of modern LLMs (like OpenAI's GPT-4o or Anthropic's Claude 3.5 Sonnet) is the ideal mechanism for this.47  
* **Workflow:**  
  1. **Define Tools:** Within the Python application, define a set of secure, auditable functions that represent the bot's capabilities (e.g., execute\_market\_order, get\_technical\_indicator, run\_forecast\_model).  
  2. **Provide Schema to LLM:** Pass the schema (name, description, parameters) of these functions to the LLM API along with a natural language prompt.49  
  3. **Receive Structured Command:** The LLM does not generate code or free text. Instead, it returns a JSON object specifying the name of the function to call and the arguments to use.52  
  4. **Execute Deterministically:** The Python application parses this JSON and calls the corresponding pre-written, validated function.  
* **Security Implications:** This pattern creates a critical security boundary. The LLM is sandboxed; it can only request actions from a predefined and approved list. It has no direct access to API keys or the execution environment, mitigating risks like prompt injection attacks that might otherwise lead to unauthorized or malicious trading activity. The LLM is an *orchestrator*, not an *executor*.

#### **3\. Risk Module Design**

This non-negotiable software module acts as the final gatekeeper for all trading operations, capable of overriding any instruction from the AI layer.

* **PnL and Cost Basis Tracking:** To make informed risk decisions, the module must accurately track performance. This requires a **FIFO (First-In, First-Out) cost basis calculation** for tax and profit reporting. This can be implemented in Python using a collections.deque to manage lots of purchased assets 53 or by adapting existing open-source calculators.54 The module must also clearly distinguish between  
  **realized PnL** (from closed trades) and **unrealized PnL** (from open positions).56  
* **Value-at-Risk (VaR) Guard:** The module should continuously calculate the portfolio's VaR, a statistical measure of potential loss. A simple but effective method is the **historical simulation VaR**, which can be calculated by taking a percentile (e.g., the 5th percentile for a 95% confidence level) of the historical return distribution of the portfolio's assets.58 The risk module would then block any new trade that would increase the portfolio's total VaR above a predefined threshold (e.g., 5% of the sub-account's capital).  
* **Drawdown Kill-Switch:** This is an essential emergency brake. The module must track the portfolio's equity high-water mark. If the current equity drops below a certain percentage of this peak (e.g., a 20% drawdown), the kill-switch is activated.10 Depending on its configuration, the switch can either block new trades (a soft stop) or liquidate all open positions and halt the bot entirely (a hard stop).61

#### **4\. Forecasting Add-ons**

To enhance the agent's decision-making, the LLM or strategy logic can call upon dedicated time-series forecasting models. These models would be exposed as "tools" for the LLM to use.

* **StatsForecast:** A high-performance Python library ideal for scalable forecasting using classical models like ARIMA and ETS. Its speed, derived from Numba JIT compilation, makes it suitable for generating rapid forecasts on the fly.62  
* **Prophet:** A Facebook library designed for ease of use and robustness in the face of seasonality, holidays, and missing data.64 It is well-suited for generating baseline forecasts with minimal tuning.65  
* **Temporal Fusion Transformer (TFT):** A state-of-the-art deep learning model for time-series forecasting. It can handle multiple time-varying inputs and static covariates, offering high accuracy but requiring significant data and computational resources for training.66

The agent could invoke these models via a function call like get\_price\_forecast(pair='BTC-EUR', horizon=24), with the results being fed back into the LLM's context to inform its next strategic suggestion.

## **Part III: Implementation, Risk Assessment, and Final Blueprint**

This final part consolidates the analysis into a practical implementation plan, addresses critical security and compliance issues, and presents a decision framework for the user.

### **E. Security & Compliance**

A robust security posture and awareness of regulatory obligations are prerequisites for deploying any automated trading system.

#### **1\. Attack Surface of the Bot Container**

The container's attack surface encompasses all potential entry points for an attacker. This includes the container image, the application code, exposed network ports, and the Docker daemon itself.68 Hardening the container is essential.

* **Use Minimal Base Images:** Start with a minimal or "distroless" base image (e.g., python:slim-bullseye) to reduce the number of installed packages, thereby minimizing the attack surface and the number of potential CVEs.70  
* **Run as Non-Root User:** The Dockerfile must include a USER directive to switch to a non-privileged user before the application starts. This is a fundamental security practice to limit the impact of a potential compromise.72  
* **Principle of Least Privilege:** Employ Docker's security options to strip the container of unnecessary permissions. This includes dropping all Linux capabilities (--cap-drop=ALL) and running with the no-new-privileges security option to prevent privilege escalation attacks.72  
* **Read-Only Filesystem:** Whenever possible, run the container with a read-only root filesystem (--read-only), mounting specific paths as temporary, writable volumes only if absolutely necessary.72  
* **Vulnerability Scanning:** Integrate automated image scanning tools like Trivy or Snyk into the build pipeline to detect known vulnerabilities in the OS packages and application dependencies before deployment.73

#### **2\. API-Withdrawal 2FA Bypass Mitigations**

The risk of API keys bypassing 2FA for withdrawals is a critical concern, especially on platforms like Bitvavo.

* **Primary Mitigation: No Withdrawal Permissions:** The most effective defense is to adhere strictly to the principle of least privilege. The API key provisioned for the automated trading bot must **never** be granted withdrawal permissions.75 All profit-taking and rebalancing should be managed through internal transfers from the sub-account to the master account, initiated by a separate, more privileged process or user.  
* **Secondary Mitigations:** In any scenario where an API key *must* have withdrawal rights, several controls are mandatory:  
  * **Strict IP Whitelisting:** The key must be restricted to a minimal set of static, trusted IP addresses.75  
  * **Address Whitelisting:** On exchanges that support it (e.g., Bybit 78, Kraken 79, Bitvavo 12), pre-approve withdrawal addresses in the account's security settings. This ensures that even if a key is compromised, funds can only be sent to a known, user-controlled address.

#### **3\. Dutch Tax/KYC Implications**

The operational nature of the proposed agent introduces a significant financial and legal risk related to Dutch taxation.

* **Box 3 vs. Box 1 Taxation:** The Dutch tax authority (Belastingdienst) distinguishes between passive investment and professional trading.  
  * **Box 3 (Wealth Tax):** Most casual investors are taxed under Box 3\. This involves a 36% tax on a *fictional* or "deemed" yield on their net assets as of January 1st each year. For 2023, this deemed yield was 6.17% for investments like crypto.80  
  * **Box 1 (Income Tax):** Activities deemed to be professional, such as active day trading, are taxed under Box 1\. In this case, the *actual profits* (capital gains) are treated as regular income and taxed at progressive rates (up to 49.50% for 2023).80  
* **Risk of Reclassification:** The design of this project—an automated, semi-autonomous, ephemeral AI agent designed to execute trades—presents a strong case for being classified as professional trading activity. A reclassification from Box 3 to Box 1 by the Belastingdienst would dramatically increase the tax burden and could render the entire strategy unprofitable.  
* **Recommendation:** It is imperative that the user consults with a Dutch tax professional to understand their specific situation and potential liability. This legal and financial due diligence is a critical prerequisite to launching the agent. KYC requirements remain tied to the master account holder and are unaffected unless a corporate account is opened.

### **F. Decision Matrix & Final Blueprint**

This section provides a structured comparison of the potential architectures and a step-by-step blueprint for implementing the recommended solution.

#### **Architecture Decision Matrix**

This matrix scores the three discussed architectures against the core project requirements. Scores are from 1 (poor) to 10 (excellent).

| Architecture | Isolation | Complexity (Higher is better) | Cost (Higher is better) | Legal Clarity | Overall Score |
| :---- | :---- | :---- | :---- | :---- | :---- |
| i. Bitvavo \+ Software Cap | 1 | 9 | 9 | 10 | 7.25 |
| ii. External Wallet → Bitvavo | 7 | 3 | 4 | 7 | 5.25 |
| **iii. Exchange with Sub-Account** | **10** | **7** | **10** | **10** | **9.25** |

**Analysis:**

* **Architecture (i)** is simple but fails completely on the core requirement of isolation, making it unacceptably risky.  
* **Architecture (ii)** improves isolation but at a high cost of operational complexity and transaction fees, and it introduces new security risks if withdrawal is automated.  
* **Architecture (iii)** is the unequivocal winner. It provides the highest possible level of exchange-enforced isolation with excellent cost-efficiency (fee-free internal transfers) and clear alignment with exchange functionalities.

#### **Security Risk Matrix for Recommended Architecture (Sub-Account Model)**

| Risk Description | Likelihood | Impact | Mitigation Strategy |
| :---- | :---- | :---- | :---- |
| Sub-account API key is compromised. | Medium | Medium | Strict least-privilege permissions (no withdrawal), IP whitelisting, secure secret management (Vault/Docker Secrets), short key lifetime. |
| Vulnerability in Freqtrade or its dependencies. | Medium | High | Use minimal base images, run regular vulnerability scans (Trivy), keep dependencies updated, run container as non-root with a read-only filesystem. |
| Container breakout to the host system. | Low | Critical | Keep Docker daemon and host OS patched, run container as non-root, use \--security-opt=no-new-privileges, drop all unnecessary capabilities. |
| LLM prompt injection causes financial loss. | Medium | Medium | Use function calling to sandbox the LLM. The LLM only suggests actions from a predefined list; it cannot execute arbitrary code or trades. All trades are validated by the deterministic risk module. |
| Tax reclassification to "professional trader". | High | High | **Consult a Dutch tax professional before deployment.** This is a legal/financial risk that cannot be mitigated technically. |

#### **Step-by-Step Implementation Blueprint**

This blueprint outlines the deployment of the recommended architecture using an exchange with sub-account support.

1. **Exchange & Account Setup:**  
   * Select and register on an exchange with a sub-account API (e.g., Binance, Kraken). Complete master account KYC.  
   * Using the master account's API key, programmatically create a new, dedicated sub-account for the bot's run.  
2. **Budgeting & Funding:**  
   * Initiate a fee-free internal transfer of the predefined budget (e.g., 500 EUR worth of USDT) from the master account to the new sub-account.  
3. **API Key Provisioning:**  
   * Programmatically generate a new API key that is explicitly scoped *only* to the newly created sub-account.  
   * Grant this key only "Read" and "Trade" permissions. **Crucially, do not grant "Withdrawal" permissions.**  
   * Apply a strict IP whitelist to the key, locking it to the static IP address of the Docker host.  
4. **Secret Management:**  
   * Store the newly generated API key and secret in the chosen secure store (e.g., docker secret create bot\_api\_key./key.txt).  
5. **Container Definition & Deployment (docker-compose.yml):**  
   YAML  
   version: '3.8'

   services:  
     trading-agent:  
       image: my-trading-agent:latest \# A pre-built, hardened image  
       container\_name: ephemeral-bot-${RUN\_ID}  
       restart: "no"  
       read\_only: true \# Run with a read-only filesystem  
       tmpfs:  
         \- /tmp  
         \- /run  
       cap\_drop:  
         \- ALL  
       security\_opt:  
         \- no\-new-privileges  
       environment:  
         \- MAX\_DRAWDOWN=0.20  
         \- TTL\_HOURS=8  
         \- STAKE\_CURRENCY=USDT  
         \- STAKE\_AMOUNT=500  
       secrets:  
         \- source: bot\_api\_key  
           target: /run/secrets/api\_key.json  
       networks:  
         \- bot-net

   secrets:  
     bot\_api\_key:  
       external: true

   networks:  
     bot-net:  
       driver: bridge

6. **Container Launch:**  
   * Launch the container using docker-compose up. The \--rm flag can be added to the docker-compose run command for automatic cleanup. The container's entrypoint script will start the Freqtrade bot, which reads its configuration from environment variables and secrets.  
7. **Execution:**  
   * The bot operates exclusively within the confines of the sub-account, controlled by its internal risk module and orchestrated by the LLM.  
8. **Automated Teardown:**  
   * The container's main process exits after its TTL expires.  
   * If launched with \--rm, the container is automatically removed.  
   * A separate, scheduled script (run on the host or a control plane) performs the final cleanup using the master API key:  
     * Transfer all remaining funds (initial budget \+ PnL) from the sub-account back to the master account.  
     * Revoke the sub-account's API key.  
     * (Optional) Delete the sub-account itself to ensure a clean slate for the next run.

### **Open Issues & Required Decisions**

The implementation of this architecture requires the end-user to make several key strategic decisions:

1. **Final Exchange Selection:** A choice must be made between Binance, Kraken, Bybit, or another suitable alternative based on factors like fees, API reliability, regulatory standing in the user's jurisdiction, and personal preference.  
2. **Risk Parameter Quantification:** The user must define their personal risk tolerance by setting concrete values for parameters like maximum drawdown percentage, Value-at-Risk limits, and per-trade risk.  
3. **Tax Status Clarification:** A consultation with a qualified Dutch tax advisor is non-negotiable to determine the likely tax treatment of the trading activities and to plan accordingly. This decision has significant financial implications.  
4. **Technology Stack Choices:**  
   * **LLM Provider:** Select a provider (e.g., OpenAI, Anthropic, Google) based on cost, performance, and API features.  
   * **Forecasting Models:** Decide on the complexity of forecasting models to integrate, balancing predictive power with implementation effort (e.g., StatsForecast for speed vs. TFT for power).  
   * **Secret Management:** Choose between the relative simplicity of Docker Secrets and the advanced security and complexity of a dedicated solution like HashiCorp Vault.

#### **Works cited**

1. Can I create a second account? \- Bitvavo Help Center, accessed on July 22, 2025, [https://support.bitvavo.com/hc/en-us/articles/4405238282769-Can-I-create-a-second-account](https://support.bitvavo.com/hc/en-us/articles/4405238282769-Can-I-create-a-second-account)  
2. Can I create a second account? – Bitvavo Help Center, accessed on July 22, 2025, [https://support.bitvavo.com/hc/en-us/articles/4405238282769-Can-I-create-a-second-account-](https://support.bitvavo.com/hc/en-us/articles/4405238282769-Can-I-create-a-second-account-)  
3. Authentication | Welcome to Bitvavo docs, accessed on July 22, 2025, [https://docs.bitvavo.com/docs/authentication/](https://docs.bitvavo.com/docs/authentication/)  
4. Authentication | Welcome to Bitvavo docs, accessed on July 22, 2025, [http://docs.bitvavo.com/docs/authentication-ws/](http://docs.bitvavo.com/docs/authentication-ws/)  
5. REST API | Welcome to Bitvavo docs, accessed on July 22, 2025, [https://docs.bitvavo.com/docs/rest-api/rest-api/](https://docs.bitvavo.com/docs/rest-api/rest-api/)  
6. What are API keys and how do I create them? \- Bitvavo Help Center, accessed on July 22, 2025, [https://support.bitvavo.com/hc/en-us/articles/4405059841809-What-are-API-keys-and-how-do-I-create-them](https://support.bitvavo.com/hc/en-us/articles/4405059841809-What-are-API-keys-and-how-do-I-create-them)  
7. Withdraw assets | Welcome to Bitvavo docs, accessed on July 22, 2025, [http://docs.bitvavo.com/docs/rest-api/withdraw-assets/](http://docs.bitvavo.com/docs/rest-api/withdraw-assets/)  
8. Terms & Conditions | Bitvavo.com, accessed on July 22, 2025, [https://bitvavo.com/en/terms](https://bitvavo.com/en/terms)  
9. Why is my Bitvavo account blocked?, accessed on July 22, 2025, [https://support.bitvavo.com/hc/en-us/articles/32542676170001-Why-is-my-Bitvavo-account-blocked](https://support.bitvavo.com/hc/en-us/articles/32542676170001-Why-is-my-Bitvavo-account-blocked)  
10. Protections \- Freqtrade, accessed on July 22, 2025, [https://www.freqtrade.io/en/2024.1/includes/protections/](https://www.freqtrade.io/en/2024.1/includes/protections/)  
11. How can I deposit (receive) crypto to Bitvavo?, accessed on July 22, 2025, [https://support.bitvavo.com/hc/en-us/articles/4405186642833-How-can-I-deposit-receive-crypto-to-Bitvavo](https://support.bitvavo.com/hc/en-us/articles/4405186642833-How-can-I-deposit-receive-crypto-to-Bitvavo)  
12. How can I add an external wallet/exchange address to the address book? \- Bitvavo Help Center, accessed on July 22, 2025, [https://support.bitvavo.com/hc/en-us/articles/4405186765201-How-can-I-add-an-external-wallet-exchange-address-to-the-address-book](https://support.bitvavo.com/hc/en-us/articles/4405186765201-How-can-I-add-an-external-wallet-exchange-address-to-the-address-book)  
13. A GUIDE TO BINANCE SUB-ACCOUNT, accessed on July 22, 2025, [https://www.binance.com/en/square/post/12695672498873](https://www.binance.com/en/square/post/12695672498873)  
14. Understanding Derivatives subaccounts \- Kraken Support, accessed on July 22, 2025, [https://support.kraken.com/articles/360042809671-understanding-derivatives-subaccounts](https://support.kraken.com/articles/360042809671-understanding-derivatives-subaccounts)  
15. FAQ — Standard Subaccount \- Bybit, accessed on July 22, 2025, [https://www.bybit.com/en/help-center/article/FAQ-Standard-Subaccount](https://www.bybit.com/en/help-center/article/FAQ-Standard-Subaccount)  
16. Create a Sub Account | Binance Open Platform, accessed on July 22, 2025, [https://developers.binance.com/docs/binance\_link/exchange-link/account](https://developers.binance.com/docs/binance_link/exchange-link/account)  
17. Create Subaccount | Kraken API Center, accessed on July 22, 2025, [https://docs.kraken.com/api/docs/rest-api/create-subaccount/](https://docs.kraken.com/api/docs/rest-api/create-subaccount/)  
18. How to use sub accounts on Bybit? \- Cryptohopper Help Center, accessed on July 22, 2025, [https://support.cryptohopper.com/en/articles/9064103-how-to-use-sub-accounts-on-bybit](https://support.cryptohopper.com/en/articles/9064103-how-to-use-sub-accounts-on-bybit)  
19. Create Api Key for Sub Account | Binance Open Platform, accessed on July 22, 2025, [https://developers.binance.com/docs/binance\_link/exchange-link/account/Create-Api-Key-for-Sub-Account](https://developers.binance.com/docs/binance_link/exchange-link/account/Create-Api-Key-for-Sub-Account)  
20. Bybit Sub-Accounts: Easy Setup & Management Guide, accessed on July 22, 2025, [https://wundertrading.com/journal/en/learn/article/sub-accounts-bybit](https://wundertrading.com/journal/en/learn/article/sub-accounts-bybit)  
21. Subaccounts | Kraken API Center, accessed on July 22, 2025, [https://docs.kraken.com/api/docs/category/rest-api/subaccounts](https://docs.kraken.com/api/docs/category/rest-api/subaccounts)  
22. Adding API Keys for Binance Sub-account to HyperTrader, accessed on July 22, 2025, [https://gethypertrader.com/support/adding-api-keys-for-binance-sub-account-to-hypertrader](https://gethypertrader.com/support/adding-api-keys-for-binance-sub-account-to-hypertrader)  
23. How to securely store secrets in Docker container?, accessed on July 22, 2025, [https://security.stackexchange.com/questions/153147/how-to-securely-store-secrets-in-docker-container](https://security.stackexchange.com/questions/153147/how-to-securely-store-secrets-in-docker-container)  
24. A Comprehensive Guide to Docker Secrets | Better Stack Community, accessed on July 22, 2025, [https://betterstack.com/community/guides/scaling-docker/docker-secrets/](https://betterstack.com/community/guides/scaling-docker/docker-secrets/)  
25. Manage sensitive data with Docker secrets, accessed on July 22, 2025, [https://docs.docker.com/engine/swarm/secrets/](https://docs.docker.com/engine/swarm/secrets/)  
26. How to Keep Docker Secrets Secure: Complete Guide \- Spacelift, accessed on July 22, 2025, [https://spacelift.io/blog/docker-secrets](https://spacelift.io/blog/docker-secrets)  
27. Understanding Kubernetes Secrets: A Comprehensive Guide \- PerfectScale, accessed on July 22, 2025, [https://www.perfectscale.io/blog/kubernetes-secrets](https://www.perfectscale.io/blog/kubernetes-secrets)  
28. Kubernetes Secrets vs Hashicorp Vault : r/devops \- Reddit, accessed on July 22, 2025, [https://www.reddit.com/r/devops/comments/ejfzhl/kubernetes\_secrets\_vs\_hashicorp\_vault/](https://www.reddit.com/r/devops/comments/ejfzhl/kubernetes_secrets_vs_hashicorp_vault/)  
29. Managing Kubernetes secrets: HashiCorp Vault vs. Azure Key Vault \- Entro Security, accessed on July 22, 2025, [https://entro.security/blog/managing-kubernetes-secrets-with-hashicorp-vault-vs-azure-key-vault/](https://entro.security/blog/managing-kubernetes-secrets-with-hashicorp-vault-vs-azure-key-vault/)  
30. Manage Kubernetes native secrets with the Vault Secrets Operator \- HashiCorp Developer, accessed on July 22, 2025, [https://developer.hashicorp.com/vault/tutorials/kubernetes-introduction/vault-secrets-operator](https://developer.hashicorp.com/vault/tutorials/kubernetes-introduction/vault-secrets-operator)  
31. Easy Container Cleanup in Cron \+ Docker Environments \- CloudBees, accessed on July 22, 2025, [https://www.cloudbees.com/blog/easy-container-cleanup-in-cron-docker-environments](https://www.cloudbees.com/blog/easy-container-cleanup-in-cron-docker-environments)  
32. Can you please suggest on best ways to cleanup docker containers \- Stack Overflow, accessed on July 22, 2025, [https://stackoverflow.com/questions/33390607/can-you-please-suggest-on-best-ways-to-cleanup-docker-containers](https://stackoverflow.com/questions/33390607/can-you-please-suggest-on-best-ways-to-cleanup-docker-containers)  
33. How to remove old Docker containers | by Harold Finch \- Medium, accessed on July 22, 2025, [https://medium.com/@haroldfinch01/how-to-remove-old-docker-containers-e98d67e1cf08](https://medium.com/@haroldfinch01/how-to-remove-old-docker-containers-e98d67e1cf08)  
34. Prune unused Docker objects \- Docker Docs, accessed on July 22, 2025, [https://docs.docker.com/engine/manage-resources/pruning/](https://docs.docker.com/engine/manage-resources/pruning/)  
35. Packet filtering and firewalls \- Docker Docs, accessed on July 22, 2025, [https://docs.docker.com/engine/network/packet-filtering-firewalls/](https://docs.docker.com/engine/network/packet-filtering-firewalls/)  
36. Block outgoing connections to private IPs from Docker containers \- Stack Overflow, accessed on July 22, 2025, [https://stackoverflow.com/questions/41107012/block-outgoing-connections-to-private-ips-from-docker-containers](https://stackoverflow.com/questions/41107012/block-outgoing-connections-to-private-ips-from-docker-containers)  
37. How do I prevent a container from making outgoing network connections? : r/docker \- Reddit, accessed on July 22, 2025, [https://www.reddit.com/r/docker/comments/hvs7n9/how\_do\_i\_prevent\_a\_container\_from\_making\_outgoing/](https://www.reddit.com/r/docker/comments/hvs7n9/how_do_i_prevent_a_container_from_making_outgoing/)  
38. Exchange-specific Notes \- Freqtrade, accessed on July 22, 2025, [https://www.freqtrade.io/en/stable/exchanges/](https://www.freqtrade.io/en/stable/exchanges/)  
39. freqtrade/freqtrade: Free, open source crypto trading bot \- GitHub, accessed on July 22, 2025, [https://github.com/freqtrade/freqtrade](https://github.com/freqtrade/freqtrade)  
40. freqtrade/docs/index.md at develop \- GitHub, accessed on July 22, 2025, [https://github.com/freqtrade/freqtrade/blob/develop/docs/index.md](https://github.com/freqtrade/freqtrade/blob/develop/docs/index.md)  
41. Jesse \- The Open-source Python Bot For Trading Cryptocurrencies, accessed on July 22, 2025, [https://jesse.trade/](https://jesse.trade/)  
42. jesse-ai/jesse: An advanced crypto trading bot written in Python \- GitHub, accessed on July 22, 2025, [https://github.com/jesse-ai/jesse](https://github.com/jesse-ai/jesse)  
43. Jesse Review \- Gainium, accessed on July 22, 2025, [https://gainium.io/bots/jesse](https://gainium.io/bots/jesse)  
44. Pricing \- Jesse.Trade, accessed on July 22, 2025, [https://jesse.trade/pricing](https://jesse.trade/pricing)  
45. ccxt \- documentation, accessed on July 22, 2025, [https://docs.ccxt.com/](https://docs.ccxt.com/)  
46. CCXT Documentation: Release 1.10.1143 | PDF | Proxy Server \- Scribd, accessed on July 22, 2025, [https://www.scribd.com/document/514832437/ccxt](https://www.scribd.com/document/514832437/ccxt)  
47. Function Calling with LLMs \- Prompt Engineering Guide, accessed on July 22, 2025, [https://www.promptingguide.ai/applications/function\_calling](https://www.promptingguide.ai/applications/function_calling)  
48. Claude 3.5: Function Calling and Tool Use \- Composio, accessed on July 22, 2025, [https://composio.dev/blog/claude-function-calling-tools](https://composio.dev/blog/claude-function-calling-tools)  
49. GPT-4.5 Function Calling Tutorial: Extract Stock Prices & News With AI | DataCamp, accessed on July 22, 2025, [https://www.datacamp.com/tutorial/gpt-4-5-function-calling](https://www.datacamp.com/tutorial/gpt-4-5-function-calling)  
50. OpenAI Function Calling Tutorial: Generate Structured Output \- DataCamp, accessed on July 22, 2025, [https://www.datacamp.com/tutorial/open-ai-function-calling-tutorial](https://www.datacamp.com/tutorial/open-ai-function-calling-tutorial)  
51. Function calling with Claude and Python \- Owl's Eyes, accessed on July 22, 2025, [https://owlseyes.net/function-calling-with-claude-and-python/](https://owlseyes.net/function-calling-with-claude-and-python/)  
52. Getting Started with GPT-4 Function Calling \- MLQ.ai, accessed on July 22, 2025, [https://blog.mlq.ai/gpt-function-calling-getting-started/](https://blog.mlq.ai/gpt-function-calling-getting-started/)  
53. Simple FIFO trading model for pnl « Python recipes « \- ActiveState Code, accessed on July 22, 2025, [https://code.activestate.com/recipes/579024-simple-fifo-trading-model-for-pnl/](https://code.activestate.com/recipes/579024-simple-fifo-trading-model-for-pnl/)  
54. Krzych0409/FIFO\_Cost\_Calculator: The FIFO Cost Calculator is a program designed to calculate the cost of revenue in sales transactions using the FIFO (First-In, First-Out) method. It efficiently computes the cost of goods sold based on purchase transactions. \- GitHub, accessed on July 22, 2025, [https://github.com/Krzych0409/FIFO\_Cost\_Calculator](https://github.com/Krzych0409/FIFO_Cost_Calculator)  
55. binfordn/capital\_gains\_calculator: Python FIFO capital gains and losses calculator \- GitHub, accessed on July 22, 2025, [https://github.com/binfordn/capital\_gains\_calculator](https://github.com/binfordn/capital_gains_calculator)  
56. How to fetch realized and unrealized profit separately using kite connect API, accessed on July 22, 2025, [https://kite.trade/forum/discussion/12392/how-to-fetch-realized-and-unrealized-profit-separately-using-kite-connect-api](https://kite.trade/forum/discussion/12392/how-to-fetch-realized-and-unrealized-profit-separately-using-kite-connect-api)  
57. Easy way to calculate Profit per trade in python \- Alpaca Community Forum, accessed on July 22, 2025, [https://forum.alpaca.markets/t/easy-way-to-calculate-profit-per-trade-in-python/1708](https://forum.alpaca.markets/t/easy-way-to-calculate-profit-per-trade-in-python/1708)  
58. Value at Risk (VaR) and Its Implementation in Python | by Serdar İlarslan | Medium, accessed on July 22, 2025, [https://medium.com/@serdarilarslan/value-at-risk-var-and-its-implementation-in-python-5c9150f73b0e](https://medium.com/@serdarilarslan/value-at-risk-var-and-its-implementation-in-python-5c9150f73b0e)  
59. Value at Risk (VaR) Calculation: Formulas, Portfolio Tools, and Methods in Python and Excel \- QuantInsti Blog, accessed on July 22, 2025, [https://blog.quantinsti.com/calculating-value-at-risk-in-excel-python/](https://blog.quantinsti.com/calculating-value-at-risk-in-excel-python/)  
60. PNL Drawdown Kill Switch Example For Strategy Builder \- NinjaTrader Ecosystem, accessed on July 22, 2025, [https://ninjatraderecosystem.com/user-app-share-download/pnl-drawdown-kill-switch-example-for-strategy-builder/](https://ninjatraderecosystem.com/user-app-share-download/pnl-drawdown-kill-switch-example-for-strategy-builder/)  
61. Build A PNL Drawdown Kill Switch Into Your NinjaTrader Bot | Strategy Builder \- YouTube, accessed on July 22, 2025, [https://www.youtube.com/watch?v=RgSqLobNuJQ](https://www.youtube.com/watch?v=RgSqLobNuJQ)  
62. End to End Walkthrough \- Nixtla \- Nixtlaverse, accessed on July 22, 2025, [https://nixtlaverse.nixtla.io/statsforecast/docs/getting-started/getting\_started\_complete.html](https://nixtlaverse.nixtla.io/statsforecast/docs/getting-started/getting_started_complete.html)  
63. Nixtla/statsforecast: Lightning ⚡️ fast forecasting with statistical and econometric models., accessed on July 22, 2025, [https://github.com/Nixtla/statsforecast](https://github.com/Nixtla/statsforecast)  
64. Prophet | Forecasting at scale. \- Meta Open Source, accessed on July 22, 2025, [https://facebook.github.io/prophet/](https://facebook.github.io/prophet/)  
65. Time Series Forecasting With Prophet in Python \- MachineLearningMastery.com, accessed on July 22, 2025, [https://machinelearningmastery.com/time-series-forecasting-with-prophet-in-python/](https://machinelearningmastery.com/time-series-forecasting-with-prophet-in-python/)  
66. Temporal Fusion Transformer-Based Trading Strategy for Multi-Crypto Assets Using On-Chain and Technical Indicators \- MDPI, accessed on July 22, 2025, [https://www.mdpi.com/2079-8954/13/6/474](https://www.mdpi.com/2079-8954/13/6/474)  
67. An AI Crystal Ball? How We Predict Future Outcomes Using a Temporal Fusion Transformer Model \- Tirabassi.com, accessed on July 22, 2025, [https://tirabassi.com/an-ai-crystal-ball-how-we-predict-future-outcomes-using-a-temporal-fusion-transformer-model/](https://tirabassi.com/an-ai-crystal-ball-how-we-predict-future-outcomes-using-a-temporal-fusion-transformer-model/)  
68. Docker Security: 6 Best Practices with Code Examples \- Spot.io, accessed on July 22, 2025, [https://spot.io/resources/container-security/docker-security-6-best-practices-with-code-examples/](https://spot.io/resources/container-security/docker-security-6-best-practices-with-code-examples/)  
69. Understanding a Containers Attack Surface | Kube by Example, accessed on July 22, 2025, [https://kubebyexample.com/learning-paths/kubernetes-security/understanding-containers-attack-surface](https://kubebyexample.com/learning-paths/kubernetes-security/understanding-containers-attack-surface)  
70. Container attack surface explained \- YouTube, accessed on July 22, 2025, [https://www.youtube.com/watch?v=mOXuCw3aPvo](https://www.youtube.com/watch?v=mOXuCw3aPvo)  
71. Introducing Docker Hardened Images: Secure, Minimal, and Ready for Production, accessed on July 22, 2025, [https://www.docker.com/blog/introducing-docker-hardened-images/](https://www.docker.com/blog/introducing-docker-hardened-images/)  
72. Docker Security \- OWASP Cheat Sheet Series, accessed on July 22, 2025, [https://cheatsheetseries.owasp.org/cheatsheets/Docker\_Security\_Cheat\_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)  
73. Docker Security: 5 Risks and 5 Best Practices for Securing Your Containers \- Tigera, accessed on July 22, 2025, [https://www.tigera.io/learn/guides/container-security-best-practices/docker-security/](https://www.tigera.io/learn/guides/container-security-best-practices/docker-security/)  
74. 8 Container Security Best Practices | Wiz, accessed on July 22, 2025, [https://www.wiz.io/academy/container-security-best-practices](https://www.wiz.io/academy/container-security-best-practices)  
75. Secure API Key Management: Best Practices \- Lucid Financials, accessed on July 22, 2025, [https://lucid.now/blog/secure-api-key-management-best-practices/](https://lucid.now/blog/secure-api-key-management-best-practices/)  
76. python-bitvavo-api/README.md at master \- GitHub, accessed on July 22, 2025, [https://github.com/bitvavo/python-bitvavo-api/blob/master/README.md](https://github.com/bitvavo/python-bitvavo-api/blob/master/README.md)  
77. How to Create and Use a Binance API Key Safely \- WunderTrading, accessed on July 22, 2025, [https://wundertrading.com/journal/en/learn/article/binance-api-key](https://wundertrading.com/journal/en/learn/article/binance-api-key)  
78. How to Manage Your Withdrawal Address Book \- Bybit, accessed on July 22, 2025, [https://www.bybit.com/en/help-center/article/How-to-Manage-Your-Withdrawal-Address-Book](https://www.bybit.com/en/help-center/article/How-to-Manage-Your-Withdrawal-Address-Book)  
79. How does two-factor authentication (2FA) for funding (deposits & withdrawals) work?, accessed on July 22, 2025, [https://support.kraken.com/articles/360000911763-how-does-two-factor-authentication-2fa-for-funding-deposits-withdrawals-work-](https://support.kraken.com/articles/360000911763-how-does-two-factor-authentication-2fa-for-funding-deposits-withdrawals-work-)  
80. Essential Guide to Crypto Tax in the Netherlands for 2025 \- TokenTax, accessed on July 22, 2025, [https://tokentax.co/blog/crypto-taxes-in-the-netherlands](https://tokentax.co/blog/crypto-taxes-in-the-netherlands)