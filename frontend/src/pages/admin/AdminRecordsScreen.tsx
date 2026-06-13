import { CalendarDays, Download } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "../../components/ui/Button";
import { Drawer } from "../../components/ui/Drawer";
import { SelectField } from "../../components/ui/SelectField";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { TextInput } from "../../components/ui/TextInput";
import { formatCurrencyINR } from "../../utils/formatters";

type RecordView = "transactions" | "policies" | "payments";

interface AdminRecordsScreenProps {
  view: RecordView;
}

/**
 * AdminRecordsScreen powers the transactions, policies, and payments table pattern.
 * It supports filters, export actions, and right-side detail drawers per row.
 */
export function AdminRecordsScreen({ view }: AdminRecordsScreenProps) {
  const [selectedRecord, setSelectedRecord] = useState<string | null>(null);

  const content = useMemo(() => {
    if (view === "transactions") {
      return {
        title: "Transactions",
        headers: ["Ref No.", "Customer", "Type", "Amount", "Status", "Date", "View"],
        rows: [
          ["TXN-HLT-20260613-AF21", "Tejas Shah", "Health", formatCurrencyINR(27258), "success", "13 Jun 2026", "View"],
          ["TXN-LIF-20260613-PQ88", "Riya Nair", "Life", formatCurrencyINR(39120), "pending", "13 Jun 2026", "View"],
        ],
      };
    }
    if (view === "policies") {
      return {
        title: "Policies",
        headers: ["Policy No.", "Customer", "Type", "Coverage", "Provider", "Issued", "View"],
        rows: [
          ["POL-HLT-20260613-AX18", "Tejas Shah", "Health", formatCurrencyINR(1000000), "Nova Life", "13 Jun 2026", "View"],
          ["POL-LIF-20260612-QW90", "Riya Nair", "Life", formatCurrencyINR(5000000), "Aegis Life", "12 Jun 2026", "View"],
        ],
      };
    }
    return {
      title: "Payments",
      headers: ["Payment Ref", "Transaction Ref", "Gateway", "Amount", "Status", "Date", "View"],
      rows: [
        ["PAY-20260613-AF21", "TXN-HLT-20260613-AF21", "Razorpay", formatCurrencyINR(27258), "success", "13 Jun 2026", "View"],
        ["PAY-20260613-PQ88", "TXN-LIF-20260613-PQ88", "Razorpay", formatCurrencyINR(39120), "pending", "13 Jun 2026", "View"],
      ],
    };
  }, [view]);

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <p className="if-eyebrow">Admin Records</p>
          <h2>{content.title}</h2>
        </div>
        <Button variant="ghost">
          <Download size={16} />
          Export
        </Button>
      </section>

      <section className="if-surface-card">
        <div className="if-admin-toolbar">
          <TextInput className="if-toolbar-search" label="Search" placeholder="Search by reference" />
          <SelectField
            label="Status"
            options={[
              { label: "All statuses", value: "all" },
              { label: "Pending", value: "pending" },
              { label: "Success", value: "success" },
              { label: "Failed", value: "failed" },
            ]}
          />
          <div className="if-date-filter">
            <CalendarDays size={18} />
            <span>01 Jun 2026 - 13 Jun 2026</span>
          </div>
          {view === "policies" ? (
            <SelectField
              label="Insurance Type"
              options={[
                { label: "All types", value: "all" },
                { label: "Health", value: "health" },
                { label: "Life", value: "life" },
                { label: "Vehicle", value: "vehicle" },
              ]}
            />
          ) : null}
        </div>

        <div className="if-table-wrap">
          <table className="if-data-table">
            <thead>
              <tr>
                {content.headers.map((header) => (
                  <th key={header}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {content.rows.map((row) => (
                <tr key={row[0]} onClick={() => setSelectedRecord(row[0])}>
                  {row.map((cell, index) => {
                    const isMono = index === 0 || (view === "payments" && index === 1);
                    const isStatus = cell === "success" || cell === "pending" || cell === "failed";
                    return (
                      <td className={isMono ? "if-mono" : ""} key={`${row[0]}-${cell}-${index}`}>
                        {isStatus ? (
                          <StatusBadge
                            status={cell === "success" ? "issued" : cell === "pending" ? "pending" : "failed"}
                          >
                            {cell.charAt(0).toUpperCase() + cell.slice(1)}
                          </StatusBadge>
                        ) : cell === "View" ? (
                          <button className="if-link-button" type="button">
                            View
                          </button>
                        ) : (
                          cell
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="if-pagination-footer">
          <button className="if-link-button" type="button">
            Previous
          </button>
          <div className="if-page-pills">
            <span className="if-page-pill is-active">1</span>
            <span className="if-page-pill">2</span>
            <span className="if-page-pill">3</span>
            <span className="if-page-pill">...</span>
            <span className="if-page-pill">12</span>
          </div>
          <button className="if-link-button" type="button">
            Next
          </button>
        </div>
      </section>

      {selectedRecord ? (
        <Drawer title={`${content.title.slice(0, -1)} detail`}>
          <div className="if-detail-stack">
            <div className="if-detail-row">
              <span>Reference</span>
              <strong className="if-mono">{selectedRecord}</strong>
            </div>
            <div className="if-detail-row">
              <span>Customer</span>
              <strong>Tejas Shah</strong>
            </div>
            <div className="if-detail-row">
              <span>Status</span>
              <StatusBadge status="issued">Success</StatusBadge>
            </div>
            <div className="if-detail-panel">
              Record detail appears here in a right-side drawer instead of page navigation.
            </div>
            <div className="if-modal-footer">
              <Button onClick={() => setSelectedRecord(null)} variant="ghost">
                Close
              </Button>
            </div>
          </div>
        </Drawer>
      ) : null}
    </div>
  );
}
