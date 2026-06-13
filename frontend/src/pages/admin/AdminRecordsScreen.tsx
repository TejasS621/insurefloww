import { CalendarDays, Download } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "../../components/ui/Button";
import { Drawer } from "../../components/ui/Drawer";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { SelectField } from "../../components/ui/SelectField";
import { Skeleton } from "../../components/ui/Skeleton";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { TextInput } from "../../components/ui/TextInput";
import { useDebouncedValue } from "../../hooks/useDebouncedValue";
import { REQUEST_DEBOUNCE_MS } from "../../services/api/config";
import { adminApi } from "../../services/api/admin";
import { normalizeApiError } from "../../utils/apiErrors";
import { formatCurrencyINR } from "../../utils/formatters";

type RecordView = "transactions" | "policies" | "payments";

interface AdminRecordsScreenProps {
  view: RecordView;
}

/**
 * AdminRecordsScreen wires table filters, pagination, and row drawers to the API.
 * Search is debounced and drawer content is fetched lazily on row click.
 */
export function AdminRecordsScreen({ view }: AdminRecordsScreenProps) {
  const [searchValue, setSearchValue] = useState("");
  const [statusValue, setStatusValue] = useState("ALL");
  const [insuranceType, setInsuranceType] = useState("ALL");
  const [page, setPage] = useState(1);
  const [records, setRecords] = useState<Array<Record<string, string | number>>>([]);
  const [total, setTotal] = useState(0);
  const [limit] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedRecord, setSelectedRecord] = useState<Record<string, string | number | null> | null>(null);
  const [detailError, setDetailError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const debouncedSearch = useDebouncedValue(searchValue, REQUEST_DEBOUNCE_MS);

  const title = useMemo(() => {
    if (view === "transactions") {
      return "Transactions";
    }
    if (view === "policies") {
      return "Policies";
    }
    return "Payments";
  }, [view]);

  useEffect(() => {
    const params = new URLSearchParams({
      page: String(page),
      limit: String(limit),
      status: statusValue,
    });
    if (debouncedSearch) {
      params.set("search", debouncedSearch);
    }
    if (view === "policies") {
      params.set("insurance_type", insuranceType);
    } else {
      params.set("date_from", "2026-06-01");
      params.set("date_to", "2026-06-30");
    }

    const loadRecords = async () => {
      setLoading(true);
      setError("");
      try {
        const response =
          view === "transactions"
            ? await adminApi.listTransactions(params)
            : view === "policies"
              ? await adminApi.listPolicies(params)
              : await adminApi.listPayments(params);

        setRecords(response.items);
        setTotal(response.total);
      } catch (requestError) {
        setError(normalizeApiError(requestError).message);
      } finally {
        setLoading(false);
      }
    };

    void loadRecords();
  }, [debouncedSearch, insuranceType, limit, page, refreshKey, statusValue, view]);

  const handleRowClick = async (reference: string) => {
    setDrawerLoading(true);
    setSelectedRecord({});
    setDetailError("");
    try {
      const detail =
        view === "transactions"
          ? await adminApi.getTransactionDetail(reference)
          : { reference, status: "Loaded", note: "Drawer detail endpoint is not yet implemented for this record type." };
      setSelectedRecord(detail);
    } catch (requestError) {
      setDetailError(normalizeApiError(requestError).message);
      setSelectedRecord(null);
    } finally {
      setDrawerLoading(false);
    }
  };

  const headers = useMemo(() => {
    if (view === "transactions") {
      return ["Ref No.", "Customer", "Type", "Amount", "Status", "Date", "View"];
    }
    if (view === "policies") {
      return ["Policy No.", "Customer", "Type", "Coverage", "Provider", "Issued", "View"];
    }
    return ["Payment Ref", "Transaction Ref", "Gateway", "Amount", "Status", "Date", "View"];
  }, [view]);

  const renderRowCells = (record: Record<string, string | number>, index: number) => {
    const formatStatus = (status: string) => {
      const s = status.toUpperCase();
      if (s === "SUCCESS" || s === "ISSUED" || s === "PAID" || s === "ACTIVE") {
        return <StatusBadge status="issued">{status}</StatusBadge>;
      }
      if (s === "PENDING" || s === "PROCESSING") {
        return <StatusBadge status="pending">{status}</StatusBadge>;
      }
      return <StatusBadge status="failed">{status}</StatusBadge>;
    };

    if (view === "transactions") {
      const ref = String(record.transaction_reference ?? record.reference ?? "N/A");
      const customer = String(record.customer_name ?? record.user_id ?? "N/A");
      const type = String(record.insurance_type ?? record.type ?? "N/A");
      const amount = formatCurrencyINR(Number(record.amount ?? record.premium_amount ?? 0));
      const status = formatStatus(String(record.status ?? "PENDING"));
      const date = String(record.date ?? (record.created_at ? new Date(record.created_at).toLocaleDateString("en-IN") : "N/A"));

      return (
        <>
          <td className="if-mono">{ref}</td>
          <td>{customer}</td>
          <td>{type}</td>
          <td>{amount}</td>
          <td>{status}</td>
          <td>{date}</td>
        </>
      );
    }

    if (view === "policies") {
      const policyNo = String(record.policy_number ?? "N/A");
      const customer = String(record.customer_name ?? record.user_id ?? "N/A");
      const type = String(record.insurance_type ?? record.type ?? "N/A");
      const coverage = formatCurrencyINR(Number(record.coverage_amount ?? 0));
      const provider = String(record.provider_name ?? record.provider ?? "N/A");
      const issued = String(record.issue_date ? new Date(record.issue_date).toLocaleDateString("en-IN") : "N/A");

      return (
        <>
          <td className="if-mono">{policyNo}</td>
          <td>{customer}</td>
          <td>{type}</td>
          <td>{coverage}</td>
          <td>{provider}</td>
          <td>{issued}</td>
        </>
      );
    }

    // Payments
    const payRef = String(record.payment_reference ?? "N/A");
    const txRef = String(record.transaction_reference ?? "N/A");
    const gateway = String(record.gateway ?? "N/A");
    const amount = formatCurrencyINR(Number(record.amount ?? 0));
    const status = formatStatus(String(record.status ?? "PENDING"));
    const date = String(record.date ?? (record.created_at ? new Date(record.created_at).toLocaleDateString("en-IN") : "N/A"));

    return (
      <>
        <td className="if-mono">{payRef}</td>
        <td className="if-mono">{txRef}</td>
        <td>{gateway}</td>
        <td>{amount}</td>
        <td>{status}</td>
        <td>{date}</td>
      </>
    );
  };

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <p className="if-eyebrow">Admin Records</p>
          <h2>{title}</h2>
        </div>
        <Button variant="ghost">
          <Download size={16} />
          Export CSV
        </Button>
      </section>

      <section className="if-surface-card">
        <div className="if-admin-toolbar">
          <TextInput
            className="if-toolbar-search"
            label="Search"
            onChange={(event) => {
              setSearchValue(event.target.value);
              setPage(1);
            }}
            placeholder="Search by reference"
            value={searchValue}
          />
          <SelectField
            label="Status"
            onChange={(event) => {
              setStatusValue(event.target.value);
              setPage(1);
            }}
            options={[
              { label: "All statuses", value: "ALL" },
              { label: "Pending", value: "PENDING" },
              { label: "Success", value: "SUCCESS" },
              { label: "Failed", value: "FAILED" },
            ]}
            value={statusValue}
          />
          <div className="if-date-filter">
            <CalendarDays size={18} />
            <span>01 Jun 2026 - 30 Jun 2026</span>
          </div>
          {view === "policies" ? (
            <SelectField
              label="Insurance Type"
              onChange={(event) => {
                setInsuranceType(event.target.value);
                setPage(1);
              }}
              options={[
                { label: "All types", value: "ALL" },
                { label: "Health", value: "HEALTH" },
                { label: "Life", value: "LIFE" },
                { label: "Vehicle", value: "VEHICLE" },
              ]}
              value={insuranceType}
            />
          ) : null}
        </div>

        {loading ? (
          <div className="if-skeleton-stack">
            <Skeleton height={56} />
            <Skeleton height={56} />
            <Skeleton height={56} />
          </div>
        ) : error ? (
          <ErrorCard message={error} onRetry={() => setRefreshKey((current) => current + 1)} />
        ) : (
          <>
            <div className="if-table-wrap">
              <table className="if-data-table">
                <thead>
                  <tr>
                    {headers.map((header) => (
                      <th key={header}>{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {records.map((record, index) => {
                    const recordReference = String(
                      record.transaction_reference ??
                        record.policy_number ??
                        record.payment_reference ??
                        `record-${index}`,
                    );
                    return (
                      <tr key={recordReference} onClick={() => void handleRowClick(recordReference)}>
                        {renderRowCells(record, index)}
                        <td>
                          <button className="if-link-button" type="button">
                            View
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="if-pagination-footer">
              <button className="if-link-button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)} type="button">
                Previous
              </button>
              <div className="if-page-pills">
                <span className="if-page-pill is-active">{page}</span>
                <span className="if-page-pill">{Math.max(1, Math.ceil(total / limit))}</span>
              </div>
              <button
                className="if-link-button"
                disabled={page >= Math.max(1, Math.ceil(total / limit))}
                onClick={() => setPage((current) => current + 1)}
                type="button"
              >
                Next
              </button>
            </div>
          </>
        )}
      </section>

      {selectedRecord ? (
        <Drawer title={`${title.slice(0, -1)} detail`} onClose={() => setSelectedRecord(null)}>
          {drawerLoading ? (
            <div className="if-skeleton-stack" style={{ padding: "24px" }}>
              <Skeleton height={24} />
              <Skeleton height={24} />
              <Skeleton height={24} />
              <Skeleton height={24} />
            </div>
          ) : detailError ? (
            <ErrorCard message={detailError} />
          ) : (
            <div className="if-detail-stack">
              {Object.entries(selectedRecord).map(([key, value]) => (
                <div className="if-detail-row" key={key}>
                  <span>{key}</span>
                  <strong className={key.toLowerCase().includes("ref") || key.toLowerCase().includes("num") || key.toLowerCase().includes("id") ? "if-mono" : ""}>
                    {String(value)}
                  </strong>
                </div>
              ))}
              <div className="if-modal-footer">
                <Button onClick={() => setSelectedRecord(null)} variant="ghost">
                  Close
                </Button>
              </div>
            </div>
          )}
        </Drawer>
      ) : null}
    </div>
  );
}
