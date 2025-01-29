INVOICE_HEADER_QUERY = '''
   SELECT inv.invoice_id
      , inv.invoice_number
      , inv.customer_id
      , inv.customer_site_id
      , inv.vendor_id
      , inv.vendor_site_id
      , inv.invoice_datetime
      , inv.action_status
      , inv.description
      , inv.remit_total
      , inv.submit_total
      , inv.invoice_number_masked
      , inv.currency_code_id
      , inv.invoice_type_id
      , inv.service_datetime
      , inv.vendor_number
      , inv.sub_type
      , (SELECT org_name FROM Org_Name WHERE org_unit_id = inv.vendor_id AND delete_flag = '0')         supplier_name
      , (SELECT org_name FROM Org_Name WHERE org_unit_id = inv.customer_id AND delete_flag = '0')       buyer_name
      , (SELECT org_name FROM Org_Name WHERE org_name_id = inv.buyer_site_name_id)                      buyer_site_name
      , (SELECT org_name FROM Org_Name WHERE org_unit_id = inv.buyer_rx_group_id AND delete_flag = '0') buyer_depart_name
      , (SELECT org_name FROM Org_Name WHERE org_name_id = inv.supplier_site_name_id)                   supplier_site_name
   FROM Invoice inv
   WHERE inv.invoice_id IN (SELECT act.document_id
     FROM Invoice inv,
          (SELECT O1.*,
               O2.vendor_id        v_vendor_id,
               O2.customer_id      v_customer_id,
               O2.created_datetime submit_datetime
          FROM Oi_Action O1,
               Oi_Action O2
          WHERE O2.document_id = O1.document_id
          AND O2.customer_id = O1.customer_id
          AND O2.action = 'Submit'
          AND O2.status = 'Submitted') act
     WHERE inv.invoice_id = act.document_id
     AND act.active_flag = '1'
     AND act.customer_id = inv.customer_id
     AND act.customer_id = :buyerId
     AND UPPER(inv.vendor_number) = UPPER(:supplierNumber)
     AND act.status NOT IN ('Saved', 'Draft')
     AND (TRUNC(act.submit_datetime) >= TO_DATE(:startDate, 'MM/DD/YYYY')
     AND TRUNC(act.submit_datetime)  <= TO_DATE(:endDate, 'MM/DD/YYYY'))
     AND ROWNUM <= 500)
'''

INVOCIE_DETAIL_QUERY = """
     SELECT detail.invoice_id
         , detail.service_datetime
         , detail.service_datetime_from
         , detail.quantity
         , detail.unit_price
         , detail.units
         , detail.description
         , detail.line_item_total
         , detail.line_item_subtotal
         , detail.qualifier
         , detail.line_item_tax_total
         , detail.line_item_description
         , (SELECT lvs.service_description
            FROM L_Vendor_Service lvs
            WHERE detail.vendor_service_id = lvs.vendor_service_id) vendor_service_desc
         , DECODE(detail.vendor_service_code, NULL, (SELECT cat.service_code
                                                     FROM Supplier_Catalog cat
                                                     WHERE cat.vendor_service_id = detail.vendor_service_id),
                  detail.vendor_service_code)                       vendor_service_code
         , icc.percentage               as                          coa_percentage
         , icc.total                    as                          coa_total
         , icc.allocation_type          as                          coa_allocation_type
         , po.po_number                 as                          coa_po_number
         , po.uuid                      as                          coa_po_uuid
         , icc.po_line_number           as                          coa_po_line_number
         , rpt.receipt_number           as                          detail_receipt_number
         , afe.afe_number               as                          coa_afe
         , ce.cost_entity_number        as                          coa_costcenter
         , ce.comments                  as                          coa_costcenter_description
         , major.major_code             as                          coa_major_code
         , major.major_code_description as                          coa_major_description
         , minor.minor_code             as                          coa_minor_code
         , minor.code_desc              as                          coa_minor_description
         , scode.subcode                as                          coa_subcode
         , scode.subcode_description    as                          coa_subcode_description
    FROM Invoice inv
             JOIN Invoice_Detail detail on inv.invoice_id = detail.invoice_id
             INNER JOIN Invoice_Coa_Coding icc
                        ON detail.invoice_detail_id = icc.invoice_detail_id AND icc.tax_type_id IS NULL
             LEFT OUTER JOIN Purchase_Order po ON icc.po_id = po.purchase_order_id
             LEFT OUTER JOIN Invoice_Detail_Receipt idr ON detail.invoice_detail_id = idr.invoice_detail_id
             LEFT OUTER JOIN Receipt rpt ON rpt.receipt_id = idr.receipt_id
             LEFT OUTER JOIN Afe afe ON icc.afe_id = afe.afe_id
             LEFT OUTER JOIN Cost_Entity ce ON icc.cost_entity_id = ce.cost_entity_id
             LEFT OUTER JOIN R_Company_Coa_Major major ON icc.company_coa_major_id = major.company_coa_major_id
             LEFT OUTER JOIN R_Company_Coa_Minor minor ON icc.company_coa_minor_id = minor.company_coa_minor_id
             LEFT OUTER JOIN R_Company_Coa_Subcode scode ON icc.company_coa_subcode_id = scode.company_coa_subcode_id
    WHERE inv.invoice_id IN (SELECT act.document_id
       FROM Invoice inv,
            (SELECT O1.*,
                    O2.vendor_id        v_vendor_id,
                    O2.customer_id      v_customer_id,
                    O2.created_datetime submit_datetime
             FROM Oi_Action O1,
                  Oi_Action O2
             WHERE O2.document_id = O1.document_id
               AND O2.customer_id = O1.customer_id
               AND O2.action = 'Submit'
               AND O2.status = 'Submitted') act
       WHERE inv.invoice_id = act.document_id
         AND act.active_flag = '1'
         AND act.customer_id = inv.customer_id
         AND act.customer_id = :buyerId
         AND act.customer_id = :buyerId
         AND UPPER(inv.vendor_number) = UPPER(:supplierNumber)
         AND act.status NOT IN ('Saved', 'Draft')
         AND (TRUNC(act.submit_datetime) >= TO_DATE(:startDate, 'MM/DD/YYYY')
           AND TRUNC(act.submit_datetime)  <= TO_DATE(:endDate, 'MM/DD/YYYY'))
         AND ROWNUM <= 500)
"""

INVOICE_HEADER_DETAIL_QUERY = """
       SELECT inv.invoice_number
         , inv.invoice_datetime
         , inv.action_status
         , inv.description
         , inv.remit_total
         , inv.submit_total
         , inv.invoice_number_masked
         , inv.service_datetime
         , inv.vendor_number
         , inv.sub_type
         , (SELECT org_name FROM Org_Name WHERE org_unit_id = inv.vendor_id AND delete_flag = '0')         supplier_name
         , (SELECT org_name FROM Org_Name WHERE org_unit_id = inv.customer_id AND delete_flag = '0')       buyer_name
         , (SELECT org_name FROM Org_Name WHERE org_name_id = inv.buyer_site_name_id)                      buyer_site_name
         , (SELECT org_name FROM Org_Name WHERE org_unit_id = inv.buyer_rx_group_id AND delete_flag = '0') buyer_depart_name
         , (SELECT org_name FROM Org_Name WHERE org_name_id = inv.supplier_site_name_id)                   supplier_site_name
         , detail.service_datetime, detail.service_datetime_from,
        detail.quantity, detail.unit_price, detail.units, detail.description, detail.line_item_total, detail.line_item_subtotal,
        detail.qualifier, detail.line_item_tax_total, detail.line_item_description,
        (SELECT lvs.service_description FROM L_Vendor_Service lvs WHERE detail.vendor_service_id = lvs.vendor_service_id) vendor_service_desc,
        DECODE(detail.vendor_service_code, NULL, (SELECT cat.service_code FROM Supplier_Catalog cat WHERE cat.vendor_service_id = detail.vendor_service_id), detail.vendor_service_code ) vendor_service_code,
        icc.percentage as coa_percentage, icc.total as coa_total, icc.allocation_type as coa_allocation_type
         , po.po_number as coa_po_number, po.uuid as coa_po_uuid, icc.po_line_number as coa_po_line_number
         , rpt.receipt_number as detail_receipt_number
         , afe.afe_number as coa_afe
         , ce.cost_entity_number as coa_costcenter
         , ce.comments as coa_costcenter_description
         , major.major_code as coa_major_code, major.major_code_description as coa_major_description
         , minor.minor_code as coa_minor_code, minor.code_desc as coa_minor_description
         , scode.subcode as coa_subcode, scode.subcode_description as coa_subcode_description
    FROM Invoice inv JOIN Invoice_Detail detail on inv.invoice_id = detail.invoice_id
                          INNER JOIN Invoice_Coa_Coding icc ON detail.invoice_detail_id = icc.invoice_detail_id AND icc.tax_type_id IS NULL
                          LEFT OUTER JOIN Purchase_Order po ON icc.po_id = po.purchase_order_id
                          LEFT OUTER JOIN Invoice_Detail_Receipt idr ON detail.invoice_detail_id = idr.invoice_detail_id
                          LEFT OUTER JOIN Receipt rpt ON rpt.receipt_id = idr.receipt_id
                          LEFT OUTER JOIN Afe afe ON icc.afe_id = afe.afe_id
                          LEFT OUTER JOIN Cost_Entity ce ON icc.cost_entity_id = ce.cost_entity_id
                          LEFT OUTER JOIN R_Company_Coa_Major major ON icc.company_coa_major_id = major.company_coa_major_id
                          LEFT OUTER JOIN R_Company_Coa_Minor minor ON icc.company_coa_minor_id = minor.company_coa_minor_id
                          LEFT OUTER JOIN R_Company_Coa_Subcode scode ON icc.company_coa_subcode_id = scode.company_coa_subcode_id
    WHERE inv.invoice_id IN (SELECT act.document_id
                             FROM Invoice inv,
                                  (SELECT O1.*,
                                          O2.vendor_id        v_vendor_id,
                                          O2.customer_id      v_customer_id,
                                          O2.created_datetime submit_datetime
                                   FROM Oi_Action O1,
                                        Oi_Action O2
                                   WHERE O2.document_id = O1.document_id
                                     AND O2.customer_id = O1.customer_id
                                     AND O2.action = 'Submit'
                                     AND O2.status = 'Submitted') act
                             WHERE inv.invoice_id = act.document_id
                               AND act.active_flag = '1'
                               AND act.customer_id = inv.customer_id
                               AND act.customer_id = :buyerId
                               AND UPPER(inv.vendor_number) = UPPER(:supplierNumber)
                               AND act.status NOT IN ('Saved', 'Draft')
                               AND (TRUNC(act.submit_datetime) >= TO_DATE(:startDate, 'MM/DD/YYYY')
                                 AND TRUNC(act.submit_datetime)  <= TO_DATE(:endDate, 'MM/DD/YYYY'))
                               AND ROWNUM <= 500)
"""    
# def getInvoiceDetailQuery() -> str:
#     return '''
#   SELECT inv.invoice_number
#          , inv.invoice_datetime
#          , inv.action_status
#          , inv.description
#          , inv.remit_total
#          , inv.submit_total
#          , inv.invoice_number_masked
#          , inv.service_datetime
#          , inv.vendor_number
#          , inv.sub_type
#          , (SELECT org_name FROM Org_Name WHERE org_unit_id = inv.vendor_id AND delete_flag = '0')         supplier_name
#          , (SELECT org_name FROM Org_Name WHERE org_unit_id = inv.customer_id AND delete_flag = '0')       buyer_name
#          , (SELECT org_name FROM Org_Name WHERE org_name_id = inv.buyer_site_name_id)                      buyer_site_name
#          , (SELECT org_name FROM Org_Name WHERE org_unit_id = inv.buyer_rx_group_id AND delete_flag = '0') buyer_depart_name
#          , (SELECT org_name FROM Org_Name WHERE org_name_id = inv.supplier_site_name_id)                   supplier_site_name
#          , detail.service_datetime, detail.service_datetime_from,
#         detail.quantity, detail.unit_price, detail.units, detail.description, detail.line_item_total, detail.line_item_subtotal,
#         detail.qualifier, detail.line_item_tax_total, detail.line_item_description,
#         (SELECT lvs.service_description FROM L_Vendor_Service lvs WHERE detail.vendor_service_id = lvs.vendor_service_id) vendor_service_desc,
#         DECODE(detail.vendor_service_code, NULL, (SELECT cat.service_code FROM Supplier_Catalog cat WHERE cat.vendor_service_id = detail.vendor_service_id), detail.vendor_service_code ) vendor_service_code,
#         icc.percentage as coa_percentage, icc.total as coa_total, icc.allocation_type as coa_allocation_type
#          , po.po_number as coa_po_number, po.uuid as coa_po_uuid, icc.po_line_number as coa_po_line_number
#          , rpt.receipt_number as detail_receipt_number
#          , afe.afe_number as coa_afe
#          , ce.cost_entity_number as coa_costcenter
#          , ce.comments as coa_costcenter_description
#          , major.major_code as coa_major_code, major.major_code_description as coa_major_description
#          , minor.minor_code as coa_minor_code, minor.code_desc as coa_minor_description
#          , scode.subcode as coa_subcode, scode.subcode_description as coa_subcode_description
#     FROM Invoice inv JOIN Invoice_Detail detail on inv.invoice_id = detail.invoice_id
#                           INNER JOIN Invoice_Coa_Coding icc ON detail.invoice_detail_id = icc.invoice_detail_id AND icc.tax_type_id IS NULL
#                           LEFT OUTER JOIN Purchase_Order po ON icc.po_id = po.purchase_order_id
#                           LEFT OUTER JOIN Invoice_Detail_Receipt idr ON detail.invoice_detail_id = idr.invoice_detail_id
#                           LEFT OUTER JOIN Receipt rpt ON rpt.receipt_id = idr.receipt_id
#                           LEFT OUTER JOIN Afe afe ON icc.afe_id = afe.afe_id
#                           LEFT OUTER JOIN Cost_Entity ce ON icc.cost_entity_id = ce.cost_entity_id
#                           LEFT OUTER JOIN R_Company_Coa_Major major ON icc.company_coa_major_id = major.company_coa_major_id
#                           LEFT OUTER JOIN R_Company_Coa_Minor minor ON icc.company_coa_minor_id = minor.company_coa_minor_id
#                           LEFT OUTER JOIN R_Company_Coa_Subcode scode ON icc.company_coa_subcode_id = scode.company_coa_subcode_id
#     WHERE inv.invoice_id IN (SELECT act.document_id
#                              FROM Invoice inv,
#                                   (SELECT O1.*,
#                                           O2.vendor_id        v_vendor_id,
#                                           O2.customer_id      v_customer_id,
#                                           O2.created_datetime submit_datetime
#                                    FROM Oi_Action O1,
#                                         Oi_Action O2
#                                    WHERE O2.document_id = O1.document_id
#                                      AND O2.customer_id = O1.customer_id
#                                      AND O2.action = 'Submit'
#                                      AND O2.status = 'Submitted') act
#                              WHERE inv.invoice_id = act.document_id
#                                AND act.active_flag = '1'
#                                AND act.customer_id = inv.customer_id
#                                AND act.customer_id = :buyerId
#                                AND UPPER(inv.vendor_number) = UPPER(:supplierNumber)
#                                AND act.status NOT IN ('Saved', 'Draft')
#                                AND (TRUNC(act.submit_datetime) >= TO_DATE(:startDate, 'MM/DD/YYYY')
#                                  AND TRUNC(act.submit_datetime)  <= TO_DATE(:endDate, 'MM/DD/YYYY'))
#                                AND ROWNUM <= 500)
#     '''
    
INVOICE_PROMPT_01="""
     I have a dataset that contains invoice headers and line items. Each row represents a line item, and multiple rows can belong to the same invoice.  The unique identifier for each invoice is the `INVOICE_NUMBER` column. 
     
     When I ask, "How many invoices are there?", group the data by the `INVOICE_NUMBER` column to count the unique invoices. Ignore duplicates or rows with missing `INVOICE_NUMBER` values.
     
     compare rows based on the following columns: `INVOICE_DATETIME`, `SERVICE_DATETIME`, `SUBMIT_TOTAL`, `COA_PO_NUMBER`, `COA_AFE`, `COA_COSTCENTER`, `COA_MAJOR_CODE`, and `COA_MINOR_CODE`.If three or more of these columns have identical values between rows, consider the invoices as potentially duplicate. 
     When I ask, "Are there duplicate invoices?", check for rows meeting this condition. Your response should be short and clear, such as:
     - "Yes, there are potentially duplicate invoices."
     - "No, there are no potentially duplicate invoices."

     Avoid explaining or including any coding logic in your response. 
     Your response should be short and clear without any additional explanation, such as: "There are X unique invoices."
     """
     
INVOICE_PROMPT_02="""
     The provoided dataset contains invoice headers and line items. Each row represents a line item, and multiple rows can belong to the same invoice.  The unique identifier for each invoice is the `INVOICE_NUMBER` column. 
     Before answering any question, ensure to consider only unique INVOICE_NUMBER values,
     
     For example:
     - When I ask "What is the total amount of all invoices?", should sum the `line_item_total` column.
     
     - When I ask "Are there duplicate invoices ?", use the invoice has given invoice number to compare other invoices based on the following columns: INVOICE_DATETIME, SERVICE_DATETIME, SUBMIT_TOTAL, COA_PO_NUMBER, COA_AFE, COA_COSTCENTER, COA_MAJOR_CODE, and COA_MINOR_CODE.
       If three or more of these columns match between not empty rows, consider the invoices as potentially duplicate. 
     #   Respond only with: 
     #   "Yes, there are potentially duplicate invoices."
     #   "No, there are no potentially duplicate invoices."
     #  - When asked, "Are there duplicate invoices for a given invoice number?", follow these steps to determine duplicates:
     #      1. Compare rows based on the following columns:
     #           Columns to Compare
     #           *INVOICE_DATETIME
     #           *SERVICE_DATETIME
     #           *SUBMIT_TOTAL
     #           *COA_PO_NUMBER
     #           *COA_AFE
     #           *COA_COSTCENTER
     #           *COA_MAJOR_CODE
     #           *COA_MINOR_CODE
     #      2. Skip Null or Empty Columns
     #           *Ignore any column that is null, empty, or missing for the rows being compared.
     #      3.Duplicate Criteria
     #           *If three or more of the remaining non-empty columns match between rows, consider the invoices as potentially duplicate. 
               
     Avoid providing coding logic or additional explanation in your response. Ensure all answers are concise and direct.
     """     
     
INVOICE_PROMPT="""
     The provoided dataset contains invoice headers and line items. Each row represents a line item, and multiple rows can belong to the same invoice.  The unique identifier for each invoice is the `INVOICE_NUMBER` column. 
     Before answering any question, ensure to consider only unique INVOICE_NUMBER values,
     
     For example:
     - When I ask "What is the total amount of all invoices?", should sum the `line_item_total` column for all uniqpue invoices.
       Respond with a concise answer, such as: "The total amount of all invoices is X."
     
     - When I ask "Are there duplicate invoices?", use the invoice has given invoice number to compare other invoices based on the following not empty or not null columns: INVOICE_DATETIME, SERVICE_DATETIME, SUBMIT_TOTAL, COA_PO_NUMBER, COA_AFE, COA_COSTCENTER, COA_MAJOR_CODE, and COA_MINOR_CODE.
       If three or more of these not empty or not null columns match between rows, consider the invoices as potentially duplicate. 
       Respond only with: 
       "Yes, there are potentially duplicate invoices." and tell what invoice number that has potential duplicates and what columns that are matching with value.
       "No, there are no potentially duplicate invoices."
               
     Avoid providing coding logic or additional explanation in your response. Ensure all answers are concise and direct.
     """       
     
     
INVOICE_PROMPT_04="""
     The provoided dataframe contains invoice headers and line items. Each row represents order header and a line item, so one or multiple rows can belong to the same invoice.  The unique identifier for each invoice is the `INVOICE_NUMBER` column. 
     General Guidelines:
      -Before answering any question, ensure to consider only unique INVOICE_NUMBER values
      -All responses should be concise, direct, and avoid explanations or coding logic
     
     Examples:
     - When user asked "Are there duplicate invoices?", process follows these steps:  
       step 1: select columns: INVOICE_DATETIME, SERVICE_DATETIME, SUBMIT_TOTAL, COA_PO_NUMBER, COA_AFE, COA_COSTCENTER, COA_MAJOR_CODE, and COA_MINOR_CODE, group the rows byusing given invoice number
       step 2: use each grouping row compare to other rows not in grouping based on only not empty or not null the following columns: INVOICE_DATETIME, SERVICE_DATETIME, SUBMIT_TOTAL, COA_PO_NUMBER, COA_AFE, COA_COSTCENTER, COA_MAJOR_CODE, and COA_MINOR_CODE. 
       setp 3: if three  not empty or not null columns match between grouping row and not in grouping rows,  consider matching invoices as potentially duplicate 
       
       if found duplicate, say "Yes, there are potentially duplicate invoices." and list all matching invoice number those have potential duplicates and what columns that are matching with value.
       otherwise, say "No, there are no potentially duplicate invoices."
       
     - When user asked "What is the total amount of all invoices?", sum the `line_item_total` column for all unique invoices,  and then respond with a concise answer.
       
     """       
     
INVOICE_PROMPT_failed="""
     The provided dataframe contains invoice headers and line items. Each row represents an order header and a line item, meaning one or multiple rows can belong to the same invoice. The unique identifier for each invoice is the `INVOICE_NUMBER` column.
     General Guidelines:
     1. Unique Invoices: 
        Before answering any question, always consider only **unique `INVOICE_NUMBER` values**, excluding duplicates and rows with missing or null `INVOICE_NUMBER`.
     2. Response Style:
        - Keep all responses concise, direct, and free from explanations or coding logic.
        - Respond clearly to the question asked without unnecessary details.
     ---
    Examples and Instructions:
     1. Checking for Duplicate Invoices:**  
     If asked, "Are there duplicate invoices?", follow these steps:  

     - Step 1:  
       Select the following columns:  
       - `INVOICE_DATETIME`  
       - `SERVICE_DATETIME`  
       - `SUBMIT_TOTAL`  
       - `COA_PO_NUMBER`  
       - `COA_AFE`  
       - `COA_COSTCENTER`  
       - `COA_MAJOR_CODE`  
       - `COA_MINOR_CODE`  

     - Step 2:
       Group rows by the given `INVOICE_NUMBER`. For each group:  
       - Compare rows within the group against rows not in the group, using only the columns that are not empty or not null.

     - Step 3:  
       If three or more non-empty or not null columns match between the grouped rows and rows outside the group, mark the invoices as potentially duplicate.

     - Respond With:**  
       - **If duplicates are found:**  
         - "Yes, there are potentially duplicate invoices."  
         - List all matching `INVOICE_NUMBER` values and specify the matching columns and their values.  

       - **If no duplicates are found:**  
         - "No, there are no potentially duplicate invoices."

     ---

     #### **2. Calculating Total Invoice Amount:**  
     If asked, *"What is the total amount of all invoices?"*:  
     - Sum the `LINE_ITEM_TOTAL` column for all unique invoices.  
     - Exclude duplicate or missing `INVOICE_NUMBER` values.  
     - **Respond With:**  
       - "The total amount of all invoices is X."

     ---

     This prompt ensures clarity, precision, and consistency, while keeping responses concise and aligned with the dataset structure.

"""    

INVOICE_PROMPT_05 = """
  You are working with two datasets:
    - The "df1" dataset contains metadata about invoices, with the column "invoice_id" being the unique identifier.
    - The "df2" dataset contains detailed line items for each invoice. The column "invoice_id" links it to the "df1" dataset.
  
  When answering questions:
    - Use the "invoice_id" column to link the two datasets.
    - If a query involves metadata (e.g., buyer name, supplier name, total amount), query "df1".
    - If a query involves items (e.g., Purchase_Order(PO), AFE, Cost Center, GL coding, product, service), query "df2".
    - If a query involves both, first query "df1" to filter invoices, then query "df2" using the filtered "invoice_id" values.
  
   For example:
     - When I ask "What is the total amount of all invoices?", should sum the 'submit_amount' from 'df1'.
       Respond with a concise answer, such as: "The total amount of all invoices is X."
     
     - When I ask "Are there duplicate invoices?",  from 'df2', use the invoice has given invoice number to compare other invoices based on the following not empty or not null columns: INVOICE_DATETIME, SERVICE_DATETIME, SUBMIT_TOTAL, COA_PO_NUMBER, COA_AFE, COA_COSTCENTER, COA_MAJOR_CODE, and COA_MINOR_CODE.
       If three or more of these not empty or not null columns match between rows, consider the invoices as potentially duplicate. 
       Respond only with: 
       "Yes, there are potentially duplicate invoices." and tell what invoice number that has potential duplicates and what columns that are matching with value.
       "No, there are no potentially duplicate invoices."
               
   Avoid providing coding logic or additional explanation in your response. Ensure all answers are concise and direct.  
"""
