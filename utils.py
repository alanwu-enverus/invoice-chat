def getInvoiceQuety() -> str:
    return '''
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
               , inv.alerts_map
               , DECODE(inv.priority_pay_flag, NULL, '0', inv.priority_pay_flag) as                              priority_pay_flag
               , (SELECT org_name FROM Org_Name WHERE org_unit_id = inv.vendor_id AND delete_flag = '0')         supplier_name
               , (SELECT org_name FROM Org_Name WHERE org_unit_id = inv.customer_id AND delete_flag = '0')       buyer_name
               , (SELECT org_name FROM Org_Name WHERE org_name_id = inv.buyer_site_name_id)                      buyer_site_name
               , (SELECT org_name FROM Org_Name WHERE org_unit_id = inv.buyer_rx_group_id AND delete_flag = '0') buyer_depart_name
               , (SELECT org_name FROM Org_Name WHERE org_name_id = inv.supplier_site_name_id)                   supplier_site_name
               , (SELECT u.last_name || ', ' || u.common_name
               FROM S_User u,
                    Oi_Action oi,
                    Invoice approvedInv
               WHERE oi.document_id = inv.invoice_id
                    AND oi.document_id = approvedInv.invoice_id
                    AND approvedInv.final_fncl_approve_datetime IS NOT NULL
                    AND oi.status = 'Approved'
                    AND oi.action = 'Approve'
                    AND NOT EXISTS (SELECT 1
                                   FROM Oi_Action o3
                                   WHERE o3.document_id = oi.document_id
                                   AND o3.sequence_number > oi.sequence_number
                                   AND o3.action = 'Unapprove'
                                   AND o3.status IN ('Submitted', 'Re-Submitted'))
                    AND (u.user_id = oi.created_by_id AND
                         ((oi.created_by_id = oi.customer_rx_id AND oi.customer_group_user_flag = '1')
                         OR (oi.created_by_id IN (-10002, -10000)))))                                        final_financial_approver
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
    
def getInvoiceDetailQuery() -> str:
    return '''
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
         , afe.property_name as coa_afe_property_name
         , afe.description as coa_afe_description
         , ce.cost_entity_number as coa_costcenter
         , ce.property_name as coa_costcenter_property_name
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
    '''