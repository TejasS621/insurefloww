import { useEffect, useMemo, useState } from "react";

import { Button } from "../components/ui/Button";
import { Drawer } from "../components/ui/Drawer";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorCard } from "../components/ui/ErrorCard";
import { SelectField } from "../components/ui/SelectField";
import { Skeleton } from "../components/ui/Skeleton";
import { StatusBadge } from "../components/ui/StatusBadge";
import { TextInput } from "../components/ui/TextInput";
import { TextareaField } from "../components/ui/TextareaField";
import { useAsyncAction } from "../hooks/useAsyncAction";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { REQUEST_DEBOUNCE_MS } from "../services/api/config";
import { adminApi, type AdminTicketSummary } from "../services/api/admin";
import { normalizeApiError } from "../utils/apiErrors";

const TAB_CONFIG = [
  { label: "All", value: "ALL" },
  { label: "Open", value: "OPEN" },
  { label: "In Progress", value: "IN_PROGRESS" },
  { label: "Resolved", value: "RESOLVED" },
] as const;

function getPriorityClass(priority: string) {
  if (priority.toUpperCase() === "HIGH" || priority.toUpperCase() === "CRITICAL") {
    return "high";
  }
  if (priority.toUpperCase() === "MEDIUM") {
    return "medium";
  }
  return "low";
}

function getStatusTone(status: string) {
  const normalizedStatus = status.toUpperCase();
  if (normalizedStatus === "RESOLVED") {
    return "issued" as const;
  }
  if (normalizedStatus === "OPEN") {
    return "pending" as const;
  }
  if (normalizedStatus === "CLOSED" || normalizedStatus === "CANCELLED") {
    return "cancelled" as const;
  }
  if (normalizedStatus === "FAILED") {
    return "failed" as const;
  }
  return "processing" as const;
}

function formatRelativeTime(dateValue: string) {
  const date = new Date(dateValue);
  if (Number.isNaN(date.getTime())) {
    return "Recently updated";
  }

  const diffMs = Date.now() - date.getTime();
  const diffMinutes = Math.max(1, Math.round(diffMs / (1000 * 60)));

  if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes === 1 ? "" : "s"} ago`;
  }

  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} hour${diffHours === 1 ? "" : "s"} ago`;
  }

  const diffDays = Math.round(diffHours / 24);
  return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`;
}

/**
 * AdminTicketsScreen keeps ticket triage on one page with a clean queue, drawer, and update actions.
 * It debounces search, lazy-loads ticket details, and keeps assignment and status updates inline.
 */
export function AdminTicketsScreen() {
  const [activeStatus, setActiveStatus] = useState<string>("ALL");
  const [searchValue, setSearchValue] = useState("");
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [tickets, setTickets] = useState<AdminTicketSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedTicket, setSelectedTicket] = useState<AdminTicketSummary | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [adminId, setAdminId] = useState("");
  const [adminResponse, setAdminResponse] = useState("");
  const [statusUpdate, setStatusUpdate] = useState("OPEN");
  const [refreshKey, setRefreshKey] = useState(0);
  const debouncedSearch = useDebouncedValue(searchValue, REQUEST_DEBOUNCE_MS);

  const assignAction = useAsyncAction();
  const updateStatusAction = useAsyncAction();

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / limit)), [limit, total]);
  const openCount = useMemo(
    () => tickets.filter((ticket) => ticket.status.toUpperCase() === "OPEN").length,
    [tickets],
  );
  const inProgressCount = useMemo(
    () => tickets.filter((ticket) => ticket.status.toUpperCase() === "IN_PROGRESS").length,
    [tickets],
  );
  const resolvedCount = useMemo(
    () => tickets.filter((ticket) => ticket.status.toUpperCase() === "RESOLVED").length,
    [tickets],
  );

  const loadTickets = async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({
        page: String(page),
        limit: String(limit),
        status: activeStatus,
      });
      if (debouncedSearch) {
        params.set("search", debouncedSearch);
      }

      const response = await adminApi.listTickets(params);
      setTickets(response.items);
      setTotal(response.total);
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadTickets();
  }, [activeStatus, debouncedSearch, limit, page, refreshKey]);

  const openTicket = async (ticketReference: string) => {
    setDetailLoading(true);
    setDetailError("");
    try {
      const ticket = await adminApi.getTicketDetail(ticketReference);
      setSelectedTicket(ticket);
      setAdminId(ticket.assigned_admin_id ?? "");
      setAdminResponse(ticket.admin_response ?? "");
      setStatusUpdate(ticket.status || "OPEN");
    } catch (requestError) {
      setDetailError(normalizeApiError(requestError).message);
      setSelectedTicket(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleAssign = async () => {
    if (!selectedTicket || !adminId.trim()) {
      return;
    }

    await assignAction.run(async () => {
      try {
        const updated = await adminApi.assignTicket(selectedTicket.ticket_reference, adminId.trim());
        setSelectedTicket(updated);
        setTickets((current) =>
          current.map((ticket) =>
            ticket.ticket_reference === updated.ticket_reference ? updated : ticket,
          ),
        );
      } catch (requestError) {
        setDetailError(normalizeApiError(requestError).message);
      }
    });
  };

  const handleStatusSave = async () => {
    if (!selectedTicket) {
      return;
    }

    await updateStatusAction.run(async () => {
      try {
        const updated = await adminApi.updateTicketStatus(
          selectedTicket.ticket_reference,
          statusUpdate,
          adminResponse,
        );
        setSelectedTicket(updated);
        setTickets((current) =>
          current.map((ticket) =>
            ticket.ticket_reference === updated.ticket_reference ? updated : ticket,
          ),
        );
      } catch (requestError) {
        setDetailError(normalizeApiError(requestError).message);
      }
    });
  };

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <p className="if-eyebrow">Admin Tickets</p>
          <h2>Support queue</h2>
        </div>
      </section>

      <section className="if-admin-ticket-summary-grid">
        <article className="if-admin-ticket-summary-card">
          <span>Open</span>
          <strong>{openCount}</strong>
        </article>
        <article className="if-admin-ticket-summary-card">
          <span>In Progress</span>
          <strong>{inProgressCount}</strong>
        </article>
        <article className="if-admin-ticket-summary-card">
          <span>Resolved</span>
          <strong>{resolvedCount}</strong>
        </article>
      </section>

      <section className="if-surface-card">
        <div className="if-admin-ticket-toolbar">
          <div className="if-pill-group">
            {TAB_CONFIG.map((tab) => (
              <button
                key={tab.value}
                className={`if-pill ${activeStatus === tab.value ? "is-active" : ""}`}
                onClick={() => {
                  setActiveStatus(tab.value);
                  setPage(1);
                }}
                type="button"
              >
                {tab.label}
              </button>
            ))}
          </div>
          <TextInput
            className="if-toolbar-search"
            label="Search Tickets"
            onChange={(event) => {
              setSearchValue(event.target.value);
              setPage(1);
            }}
            placeholder="Search by reference or subject"
            value={searchValue}
          />
        </div>
      </section>

      {loading ? (
        <section className="if-ticket-stack">
          <Skeleton height={128} />
          <Skeleton height={128} />
          <Skeleton height={128} />
        </section>
      ) : error ? (
        <ErrorCard message={error} onRetry={() => setRefreshKey((current) => current + 1)} />
      ) : tickets.length === 0 ? (
        <EmptyState
          title="No tickets matched these filters"
          description="Try changing the status filter or search term to load support requests."
        />
      ) : (
        <>
          <section className="if-ticket-stack">
            {tickets.map((ticket) => (
              <article className="if-admin-ticket-card" key={ticket.ticket_reference}>
                <div className={`if-priority-rail is-${getPriorityClass(ticket.priority)}`} />
                <div className="if-admin-ticket-main">
                  <div className="if-admin-ticket-copy">
                    <div className="if-admin-ticket-title-row">
                      <span className="if-mono if-admin-ticket-ref">{ticket.ticket_reference}</span>
                      <h3>{ticket.subject}</h3>
                    </div>
                    <p className="if-admin-ticket-customer">Customer ID: {ticket.user_id}</p>
                    <div className="if-admin-ticket-badges">
                      <StatusBadge status="processing">{ticket.category}</StatusBadge>
                      <StatusBadge
                        status={
                          getPriorityClass(ticket.priority) === "high"
                            ? "failed"
                            : getPriorityClass(ticket.priority) === "medium"
                              ? "pending"
                              : "processing"
                        }
                      >
                        {ticket.priority}
                      </StatusBadge>
                      <StatusBadge status={getStatusTone(ticket.status)}>{ticket.status}</StatusBadge>
                      <span className="if-admin-ticket-time">{formatRelativeTime(ticket.updated_at)}</span>
                    </div>
                  </div>

                  <div className="if-admin-ticket-actions">
                    <Button onClick={() => void openTicket(ticket.ticket_reference)} variant="ghost">
                      Open Ticket
                    </Button>
                  </div>
                </div>
              </article>
            ))}
          </section>

          <div className="if-pagination-footer">
            <button
              className="if-link-button"
              disabled={page <= 1}
              onClick={() => setPage((current) => current - 1)}
              type="button"
            >
              Previous
            </button>
            <div className="if-page-pills">
              <span className="if-page-pill is-active">{page}</span>
              <span className="if-page-pill">{totalPages}</span>
            </div>
            <button
              className="if-link-button"
              disabled={page >= totalPages}
              onClick={() => setPage((current) => current + 1)}
              type="button"
            >
              Next
            </button>
          </div>
        </>
      )}

      {detailLoading ? (
        <Drawer title="Ticket detail" width="wide">
          <div className="if-detail-stack">
            <Skeleton height={32} />
            <Skeleton height={32} />
            <Skeleton height={120} />
          </div>
        </Drawer>
      ) : selectedTicket ? (
        <Drawer title="Ticket detail" width="wide" onClose={() => setSelectedTicket(null)}>
          <div className="if-detail-stack">
            {detailError ? <ErrorCard message={detailError} /> : null}

            <section className="if-admin-ticket-detail-panel">
              <div className="if-detail-row">
                <span>Ticket</span>
                <strong className="if-mono">{selectedTicket.ticket_reference}</strong>
              </div>
              <div className="if-detail-row">
                <span>Customer</span>
                <strong>{selectedTicket.user_id}</strong>
              </div>
              <div className="if-detail-row">
                <span>Status</span>
                <StatusBadge status={getStatusTone(selectedTicket.status)}>{selectedTicket.status}</StatusBadge>
              </div>
              <div className="if-detail-row">
                <span>Category</span>
                <strong>{selectedTicket.category}</strong>
              </div>
              <div className="if-detail-row">
                <span>Priority</span>
                <strong>{selectedTicket.priority}</strong>
              </div>
            </section>

            <section className="if-admin-ticket-form-panel">
              <h3 className="if-admin-ticket-panel-title">Customer message</h3>
              <blockquote className="if-ticket-quote">{selectedTicket.message}</blockquote>
            </section>

            <section className="if-admin-ticket-form-panel">
              <h3 className="if-admin-ticket-panel-title">Assignment</h3>
              <TextInput
                label="Assign Admin"
                onChange={(event) => setAdminId(event.target.value)}
                placeholder="Enter admin identifier"
                value={adminId}
              />
              <div className="if-table-action-row">
                <Button loading={assignAction.isLoading} onClick={() => void handleAssign()}>
                  Assign Ticket
                </Button>
              </div>
            </section>

            <section className="if-admin-ticket-form-panel">
              <h3 className="if-admin-ticket-panel-title">Response and status</h3>
              <TextareaField
                label="Admin response"
                onChange={(event) => setAdminResponse(event.target.value)}
                placeholder="Type your response"
                rows={5}
                value={adminResponse}
              />
              <div className="if-admin-ticket-status-grid">
                <SelectField
                  label="Status update"
                  onChange={(event) => setStatusUpdate(event.target.value)}
                  options={[
                    { label: "Open", value: "OPEN" },
                    { label: "In Progress", value: "IN_PROGRESS" },
                    { label: "Resolved", value: "RESOLVED" },
                    { label: "Closed", value: "CLOSED" },
                  ]}
                  value={statusUpdate}
                />
                <div className="if-drawer-save">
                  <Button loading={updateStatusAction.isLoading} onClick={() => void handleStatusSave()}>
                    Save Update
                  </Button>
                </div>
              </div>
            </section>

            <div className="if-modal-footer">
              <Button onClick={() => setSelectedTicket(null)} variant="ghost">
                Close
              </Button>
            </div>
          </div>
        </Drawer>
      ) : null}
    </div>
  );
}
