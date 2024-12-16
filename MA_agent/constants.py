import MA_agent.prompts as prompts

LIST_OF_DOCUMENTS_INPUT = """
1. Accounts Receivable & Payable
2. Audited Financial Statement
3. Debt & Capital Structure Details
4. Financial Projections & Forecast
5. Tax Returns
6. Articles of Incorporation & Bylaws
7. IP Documentation
8. Litigation & Dispute History
9. Material Contracts & Agreements
10. Regulatory Compliance & Permits
"""

LIST_OF_DOCUMENTS_OUTPUT = [
    "NDA",
    "Due Diligence",
    "Term Sheet",
    "Letter of Intent",
    "Definitive Agreement",
]

DOCUMENT_PROMPT_MAPPING = {
    "NDA": prompts.PROMPT_NDA,
    "Due Diligence": prompts.PROMPT_DUE_DILIGENCE,
    "Term Sheet": prompts.PROMPT_TERM_SHEET,
    "Letter of Intent": prompts.PROMPT_LETTER_OF_INTENT,
    "Definitive Agreement": prompts.PROMPT_DEFINITIVE_AGREEMENT,
}
