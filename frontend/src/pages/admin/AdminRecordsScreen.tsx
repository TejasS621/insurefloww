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
    setDetailError("");
    try {
      const detail =
        view === "transactions"
          ? await adminApi.getTransactionDetail(reference)
          : { reference, status: "Loaded", note: "Drawer detail endpoint is not yet implemented for this record type." };
      setSelectedRecord(detail);
    } catch (requestError) {
      setDetailError(normalizeApiError(requestError).message);
    }
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
          Export
        </Button>
      </section>

      <section className="if-surface-card">
        <div className="if-admin-toolbar">
          <TextInput
            className="if-toolbar-search"
            label="Search"
            onChange={(event) => setSearchValue(event.target.value)}
            placeholder="Search by reference"
            value={searchValue}
          />
          <SelectField
            label="Status"
            onChange={(event) => setStatusValue(event.target.value)}
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
              onChange={(event) => setInsuranceType(event.target.value)}
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
                    {Object.keys(records[0] ?? { reference: "Reference", status: "Status" }).map((header) => (
                      <th key={header}>{header}</th>
                    ))}
                    <th>View</th>
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
                        {Object.entries(record).map(([key, value]) => (
                          <td className={key.includes("reference") || key.includes("number") ? "if-mono" : ""} key={key}>
                            {typeof value === "string" && value.toLowerCase() === "success" ? (
                              <StatusBadge status="issued">Success</StatusBadge>
                            ) : typeof value === "string" && value.toLowerCase() === "pending" ? (
                              <StatusBadge status="pending">Pending</StatusBadge>
                            ) : typeof value === "string" && value.toLowerCase() === "failed" ? (
                              <StatusBadge status="failed">Failed</StatusBadge>
                            ) : (
                              String(value)
                            )}
                          </td>
                        ))}
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
        <Drawer title={`${title.slice(0, -1)} detail`}>
          {detailError ? (
            <ErrorCard message={detailError} />
          ) : (
            <div className="if-detail-stack">
              {Object.entries(selectedRecord).map(([key, value]) => (
                <div className="if-detail-row" key={key}>
                  <span>{key}</span>
                  <strong className={key.includes("reference") || key.includes("number") ? "if-mono" : ""}>
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
