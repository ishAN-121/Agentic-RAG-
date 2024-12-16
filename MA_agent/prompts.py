PROMPT_TERM_SHEET = """
**Objective:** Create a term sheet outlining the key terms and conditions for the proposed merger or acquisition between {company_a} and {company_b}. Use the provided company information and specified outline.

**Inputs:**

1. **{company_a} Details:**  
    {company_a_details}

2. **{company_b} Details:**  
    {company_b_details}

3. **Document Outline (Markdown format):**  
    {document_outline}
    
4. **Instructions:**
    {instructions}

**Task:**

Using the above inputs, draft a term sheet following the provided outline. The document should succinctly summarize the key financial, legal, and operational terms of the transaction. Ensure clarity and precision in outlining the structure, valuation, conditions, and commitments of the deal, all formatted according to the specified Markdown outline.
"""

PROMPT_DEFINITIVE_AGREEMENT = """
**Objective:** Write a definitive agreement for the merger/acquisition between {company_a} and {company_b} using the provided company details and outline.

**Inputs:**

1. **{company_a} Details:**  
    {company_a_details}

2. **{company_b} Details:**  
    {company_b_details}  

3. **Document Outline (Markdown format):**  
    {document_outline}
    
4. **Instructions:**
    {instructions}

**Task:**

Using the above inputs, draft a definitive agreement following the given outline. Ensure the agreement accurately reflects the business and legal considerations necessary for the merger/acquisition, and is formatted according to the specified Markdown outline.
"""

PROMPT_LETTER_OF_INTENT = """
**Objective:** Write a Letter of Intent to outline the preliminary terms and intentions for the merger or acquisition between {company_a} and {company_b}. Use the provided company details and the specified outline format.

**Inputs:**

1. **{company_a} Details:**  
    {company_a_details}

2. **{company_b} Details:**  
    {company_b_details}

3. **Document Outline (Markdown format):**  
    {document_outline}

4. **Instructions:**
    {instructions}

**Task:**

Utilizing the inputs above, draft a Letter of Intent that aligns with the provided outline. This document should clearly express the intentions of both parties regarding the key aspects of the proposed transaction, including objectives, transaction structure, valuation, confidentiality, and any other preliminary terms. Ensure it is clearly formatted according to the specified Markdown outline.
"""

PROMPT_NDA = """
**Objective:** Write a Non-Disclosure Agreement to protect confidential information exchanged between {company_a} and {company_b} during the merger or acquisition discussions. Use the provided company details and the specified outline format. 

**Inputs:**

1. **{company_a} Details:**  
    {company_a_details}

2. **{company_b} Details:**  
    {company_b_details}

3. **Document Outline (Markdown format):**  
    {document_outline}

4. **Instructions:**
    {instructions}
**Task:**

Using the inputs above, draft a Non-Disclosure Agreement following the provided outline. This document should specify the obligations of both parties concerning the confidentiality of any proprietary information shared during the merger or acquisition process. Ensure to include key elements such as the definition of confidential information, duration of confidentiality, permitted disclosures, and any penalties for breaches. Format the NDA according to the specified Markdown outline.
"""

PROMPT_DUE_DILIGENCE = """
**Objective:** Prepare a Due Diligence Request List to gather necessary information and documents from {company_a} and {company_b} for the merger or acquisition process. Use the provided company details and specified outline format.

**Inputs:**

1. **{company_a} Details:**  
    {company_a_details}

2. **{company_b} Details:**  
    {company_b_details}

3. **Document Outline (Markdown format):**  
    {document_outline}

4. **Instructions:**
    {instructions}
**Task:**

Using the inputs above, draft a Due Diligence Request List following the provided outline. This document should detail all essential documents and information needed to thoroughly assess the business, financial, legal, and operational aspects of both companies. Ensure to cover all relevant categories, such as financial records, legal documents, intellectual property, contracts, regulatory compliance, and human resources. Format the request list according to the specified Markdown outline.
"""

SUMMARY_PROMPT = """
You are an expert in mergers and acquisitions. Your task is to create a comprehensive summary and key insights for a specific merger or acquisition document. The summary must be based on detailed company documentation and should not omit any crucial information. Here’s what you need to do:

**Input:**
1. **Company Name:** {company_name}
2. **Document Type:** {document_type}
3. **Context and Information:** {context}

**Output:**

Produce a single, cohesive narrative that combines both the summary and key insights derived from the provided documentation. Include all pertinent information related to the financials, strategic advantages, potential risks, compliance matters, and any other relevant elements specific to the document type.

---

**Example:**

**Input:**
- **Company Name:** XYZ Corp
- **Document Type:** Due Diligence
- **Context and Information:** 
  - Healthy accounts receivable with consistent cash flow.
  - Audited financial statements show steady revenue growth over the past 3 years.
  - Moderate debt levels with a strong equity position.
  - Financial projections indicate a 10% growth annually.
  - Tax returns have been consistently accurate with no outstanding issues.
  - Articles of Incorporation align with state regulations.
  - Strong patent portfolio with five registered patents.
  - No current litigation, but a history of minor disputes resolved amicably.
  - All material contracts are up-to-date with favorable terms.

**Output:**

XYZ Corp's Due Diligence review highlights the XYZ Corp's being in strong financial health, underscored by steady revenue growth and robust equity standing. The company's consistent cash flow and prudent debt levels suggest a reliable financial foundation. Projected growth of 10% annually aligns well with industry trends, reinforcing market competitiveness. XYZ Corp's clean litigation history and regulatory compliance minimize potential legal risks, while its strong portfolio of five registered patents offers significant strategic leverage for future innovation and competitive advantage. Favorable terms in the current material contracts further support potential synergies in post-acquisition scenarios.
"""


INSIGHTS_PROMPT = """
You are an expert analyst tasked with evaluating the potential merger/acquisition between {company_a} and {company_b} following the important instructions {instructions}. Using the provided financial and legal documents, generate a comprehensive analysis focusing on the following key areas:

1. **Financial Risk Assessment**: Evaluate the financial stability and risks associated with the merger/acquisition.
2. **Operational Compatibility**: Assess how well the operational processes and systems of the two companies align.
3. **Cultural Considerations**: Analyze the cultural fit between the two organizations and potential challenges.
4. **Regulatory Compliance**: Identify any regulatory hurdles or compliance issues that may arise.

Please provide your insights in the form of a JSON object with the following structure:

{{
  "financial_risk_assessment": "Your analysis here",
  "operational_compatibility": "Your analysis here",
  "cultural_considerations": "Your analysis here",
  "regulatory_compliance": "Your analysis here"
}}

**Context:**

- **{company_a}**: {a_summary}
- **{company_b}**: {b_summary}

---

**Example Output:**


{{
  "financial_risk_assessment": "Company A has a strong balance sheet, but Company B's recent losses pose a risk. The combined entity may face cash flow challenges.",
  "operational_compatibility": "Both companies use similar ERP systems, which should ease integration. However, differences in supply chain management could pose challenges.",
  "cultural_considerations": "Company A has a hierarchical culture, while Company B is more collaborative. This may lead to initial friction among employees.",
  "regulatory_compliance": "The merger will require approval from the European Commission due to market share concerns in the EU."
}}

DO NOT wrap the output in ```json``` markdown
"""


METRICS_PROMPT = """
You are an expert analyst tasked with evaluating the potential merger/acquisition between {company_a} and {company_b} following the important instructions {instructions}. Using the provided financial, operational, and cultural data, generate a comprehensive evaluation focusing on the following key metrics:

1. **Accountability & Oversight**: Rate the effectiveness of governance structures, leadership frameworks, and accountability mechanisms in the context of the merger/acquisition.
2. **Ethical Standards**: Rate the alignment of ethical values and practices between the two companies.
3. **Cultural Compatibility**: Rate the compatibility of cultural values, work environments, and organizational practices between the two companies.
4. **Overall Alignment**: Provide an overall rating of how well the two companies align across all dimensions, including strategic objectives, values, and operational synergies.

Each metric should be rated on a scale of **1 to 5**, where:
- **1**: Very poor alignment or significant challenges.
- **2**: Poor alignment with several issues to address.
- **3**: Moderate alignment with some challenges.
- **4**: Good alignment with minor challenges.
- **5**: Excellent alignment with little to no challenges.

Please provide your insights in the form of a JSON object with the following structure:

{{
  "accountability_oversight": "Your rating here (1-5)",
  "ethical_standards": "Your rating here (1-5)",
  "cultural_compatibility": "Your rating here (1-5)",
  "overall_alignment": "Your rating here (1-5)"
}}

**Context:**

- **{company_a}**: {a_summary}
- **{company_b}**: {b_summary}

DO NOT wrap the output in ```json``` markdown
"""
