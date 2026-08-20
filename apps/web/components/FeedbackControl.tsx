"use client";

import { MessageSquare, X } from "lucide-react";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export default function FeedbackControl() {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">(
    "idle",
  );
  const [message, setMessage] = useState("");
  const [category, setCategory] = useState("general");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setState("sending");
    try {
      await api("/feedback", {
        method: "POST",
        body: JSON.stringify({
          category,
          message,
          page_path: window.location.pathname,
        }),
      });
      setState("sent");
      setMessage("");
    } catch {
      setState("error");
    }
  }

  return (
    <>
      <button
        className="button feedback-fab"
        onClick={() => setOpen(true)}
        aria-label="Send feedback"
      >
        <MessageSquare size={17} /> Feedback
      </button>
      {open && (
        <div
          className="modal-backdrop"
          role="presentation"
          onMouseDown={() => setOpen(false)}
        >
          <section
            className="modal card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="feedback-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="card-head">
              <div>
                <span className="eyebrow">Product feedback</span>
                <h2
                  id="feedback-title"
                  style={{ fontSize: "1.8rem", margin: 0 }}
                >
                  What did you notice?
                </h2>
              </div>
              <button
                className="button ghost"
                onClick={() => setOpen(false)}
                aria-label="Close feedback"
              >
                <X size={20} />
              </button>
            </div>
            {state === "sent" ? (
              <div className="empty-state">
                <div>
                  <h3>Thank you.</h3>
                  <p className="muted">Your feedback is in the review queue.</p>
                  <button className="button" onClick={() => setOpen(false)}>
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <form className="form-grid" onSubmit={submit}>
                <label>
                  Category
                  <select
                    value={category}
                    onChange={(event) => setCategory(event.target.value)}
                  >
                    <option value="general">General</option>
                    <option value="feature">Feature idea</option>
                    <option value="usability">Usability</option>
                    <option value="data_issue">Report a data issue</option>
                  </select>
                </label>
                <label>
                  Message
                  <textarea
                    required
                    minLength={3}
                    maxLength={2000}
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                    placeholder="Tell us what you expected and what happened."
                  />
                </label>
                {state === "error" && (
                  <p className="form-message error">
                    Feedback could not be sent. Try again.
                  </p>
                )}
                <button className="button" disabled={state === "sending"}>
                  {state === "sending" ? "Sending…" : "Send feedback"}
                </button>
              </form>
            )}
          </section>
        </div>
      )}
    </>
  );
}
