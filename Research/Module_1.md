# **Understand how digital banking actually works** 

Digital banking is the **delivery of banking services through digital channels** such as mobile apps, websites, ATMs, and online platforms, allowing customers to manage their finances without visiting a physical bank branch. 

## **With digital banking, you can:** 

- Check account balances and transaction history. Transfer money between accounts or to other people. Pay bills and recharge mobile phones. Apply for loans, credit cards, or fixed deposits. Deposit checks electronically. 

- Receive real-time notifications for transactions. 

## **Benefits** 

- Convenience: Bank anytime, anywhere. Speed: Transactions are processed quickly. 

- 24/7 access: Services are available even outside banking hours. Lower costs: Often reduces fees and paperwork. 

- Security: Uses features such as encryption, passwords, biometric authentication, and one-time passwords (OTPs). 

# **Core Banking System (CBS)** 

CBS bank ka "main brain" hai, jahan har customer ka account aur har transaction record hota hai. 

A banking core system (also called a core banking system or CBS) is the central software platform that **manages a bank's essential operations and customer accounts** . It acts as the "heart" of a bank, ensuring that all branches, ATMs, mobile apps, internet banking, and other channels access the same customer and account information in real time. 

## **What a core banking system does** 

A core banking system handles the bank's day-to-day operations, including: Customer management: Stores customer profiles and KYC information. Account management: Maintains savings, current, and fixed deposit accounts. Transaction processing: Processes deposits, withdrawals, transfers, and payments. 



<!-- Start of picture text -->
Mobile App / ATM /<br>UPI / Internet<br>Banking<br><!-- End of picture text -->



<!-- Start of picture text -->
API Gateway<br>Core Banking<br>System (CBS)<br>Transactions<br>Customer<br>Accounts<br>Database<br><!-- End of picture text -->

Loan management: Manages loan applications, repayments, interest calculations, and schedules. 

Interest and fee calculations: Automatically calculates interest, charges, and penalties. 

General ledger: Records financial transactions for accounting. 

Reporting and compliance: Generates regulatory reports and supports audits. **How it works** 

When a customer performs a transaction, such as transferring money through a mobile banking app: 

The request is sent to the core banking system. 

The system verifies the account balance and applicable rules. It updates the sender's and recipient's accounts. It records the transaction in the bank's ledger. It sends the confirmation back to the app. 

# **Payment Rails** 

Payment rails are the underlying networks and infrastructure that **move money from one account to another** . They define how a payment is transmitted, processed, settled, and confirmed between banks, payment providers, and customers. 

|**Payment Rail**|**Typical Use**|**Speed**|
|---|---|---|
|Bank transfers (ACH, NEFT,<br>etc.)|Payroll, bills, account<br>transfers|Hours to days (varies)|
|Real-time payment rails (UPI,<br>RTP, FedNow)|Instant person-to-person<br>and merchant payments|Seconds|
|Card networks (Visa,<br>Mastercard, RuPay)|Debit and credit card<br>purchases|Authorization in seconds;<br>settlement later|
|Wire transfers|Large-value domestic and<br>international transfers|Minutes to hours|
|International payment<br>networks (SWIFT)|Cross-border payments|Hours to several days|



## **How payment rails work** 

When you send money: You initiate a payment (through a banking app, card, or wallet). 

The payment travels over a payment rail. Banks or payment providers verify the transaction. 

The payment is settled between financial institutions. The recipient receives the funds. 

**Characteristics of payment rails** Different payment rails vary in: Speed (instant vs. next day) Cost (fees charged to banks, merchants, or users) Availability (24/7 or business hours only) Transaction limits 

Geographic reach (domestic or international) Security and fraud protection 

**RBI** 

# **NPCI** 

NPCI stands for the National Payments Corporation of India. It is the main group that **manages all digital** . **money transfers and retail payment systems in India** The Reserve Bank of India (RBI) and the Indian Banks’ Association (IBA) created it in 2008. 

## **Major Services Provided** 

**UPI (Unified Payments Interface):** Allows instant, real-time mobile money transfers between different bank accounts using virtual addresses or QR codes. **RuPay:** An Indian domestic card network for ATM, debit, and credit cards, built to rival foreign networks like Visa and Mastercard. 

**IMPS (Immediate Payment Service):** Provides instant 24/7 interbank electronic fund transfers. **FASTag:** An electronic toll collection system used on national highways via RFID technology. **Bharat Bill Payment System (BBPS):** A unified platform for paying recurring bills like electricity, water, and gas. 

RBI stands for the Reserve Bank of India, the central bank of the country. It **manages currency, controls monetary policy, and regulates all banks in India.** 

## **Main Functions** 

Regulates banks and financial institutions. Issues and manages the Indian Rupee. Sets monetary policy (such as repo rates). Oversees payment systems and financial stability. Authorizes and supervises organizations like NPCI. 

RBI │ Regulates & oversees │ NPCI │ ┌─────────┴─────────┐ │ │ UPI                                                                 IMPS 

|**Feature**|**IMPS**|**NEFT**|**RTGS**|
|---|---|---|---|
|**Full form**|Immediate Payment<br>Service|National Electronic<br>Funds Transfer|Real Time Gross<br>Settlement|
|**Transfer speed**|Instant|Usually within<br>minutes|Instant (real-time)|
|**Availability**|24×7|24×7|24×7|
|**Settlement**|Immediate|Processed in<br>batches|Individual<br>transaction settled<br>immediately|
|**Minimum**<br>**amount**|No minimum|No minimum|₹2 lakh minimum|
|**Best for**|Urgent small to<br>medium transfers|Routine transfers|High-value transfers<br>(₹2 lakh and above)|



## **When to use IMPS** 

You need the recipient to receive money immediately. You're making an urgent payment. 

## **When to use NEFT** 

The payment isn't timecritical. You're transferring a larger amount (subject to your bank's limits). 

## **When to use RTGS** 

You need to transfer ₹2 lakh or more. The transfer is urgent and must be settled immediately. You're making high-value payments, such as property purchases or large business transactions. 

# **Card Network** 

A card network is the **organization that connects card issuers (banks), merchants, and merchant-acquiring banks so card payments can be authorized, processed, and settled.** When you swipe, tap, or enter your card online, the card network routes the payment request between the merchant and your bank. 

## **What a card network does** 

Routes payment messages between banks. Verifies that the card is valid. 

Applies security standards (such as EMV chip and tokenization). Defines operating rules for participating banks. Calculates interchange and settlement between banks. Helps manage fraud and disputes. 

|**Card Network**|**Where it's used**|**Notes**|
|---|---|---|
|Visa|Worldwide|Largest global card network.|
|Mastercard|Worldwide|Accepted in most countries.|
|American Express|Worldwide|Often acts as both network and card<br>issuer.|
|Discover Financial Services|Primarily U.S.|Limited international acceptance<br>compared to Visa and Mastercard.|
|RuPay|India (and expanding internationally)|India's domestic card network<br>operated by National Payments|



° 

° 



<!-- Start of picture text -->
n n<br>Request Request Request<br>initiate ane forward forward a<br>Response 2) 000° /s vent<br>_. Passed to : NPCI UPI Re 7<br>Mobile App PAYER SERVER PAYEE<br>= PSP PSP<br>c= NPCI passes request<br>USER Debits account to bank to credit<br>& response back<br>de _—« to. UPI ~<br>REMITTER BENEFICIARY<br>BANK BANK<br><!-- End of picture text -->

@ 

@ 

e 

e 

e 

e 

e 

e 

## **Responsibilities of the Involved Parties** 

Payer PSP 

Customer onboarding 

To create a UPI ID 

Create device binding (first-factor authentication) Payee PSP 

On-board customer/merchant 

## Remitter Bank 

Hold & Debit Bank account for the transaction Store and verify UPI PIN Beneficiary Bank 

Process incoming credits and funds into the beneficiary account 

Facilitate money transfer/payment to the recipient using UPI 

## **How Safe Is It?** 

With the growing digitalization, it's just to make sure that the transaction you're doing is safe. While performing any UPI transaction, there are chances that phishers may try to breach and do any fraudulent activities. To answer this here's a quick guide to prevent any unavoided actions. 

You must always avoid sharing your credentials (such as PIN, Password, or any sensitive information) Never save your card details (debit/credit) while performing any transaction 

There are a bunch of fraud apps available in the market today, avoid downloading them on your phone as they might get access to your wallet or other related apps. 

If you're about to receive any funds, perform safe methods for doing so (such as QR, Phone numbers only) and ensure that you're not sharing any OTP 

Certain cases have been reported of fraudulent activities (such as cloning, unsecured links, etc.) so it's best to avoid visiting such websites. 

