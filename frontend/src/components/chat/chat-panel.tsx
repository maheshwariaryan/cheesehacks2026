"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { getChatHistory, sendChatMessage, clearChat } from "@/lib/api";
import { ChatMessage } from "@/lib/types";
import {
    Send, RotateCcw, Bot, User, ChevronDown, ChevronUp,
    FileText, Sparkles, MessageSquare, Zap, TrendingUp,
    AlertTriangle, DollarSign, HelpCircle, BookOpen, ArrowRight
} from "lucide-react";

// ─── Suggestion groups for empty state ────────────────────────────────────────
const SUGGESTION_GROUPS = [
    {
        label: "Earnings Quality",
        icon: TrendingUp,
        questions: [
            "What's the adjusted EBITDA and what adjustments were made?",
            "Are revenue streams recurring or one-time in nature?",
            "What is the earnings sustainability rating and why?",
        ],
    },
    {
        label: "Risk & Red Flags",
        icon: AlertTriangle,
        questions: [
            "What are the biggest red flags identified in this deal?",
            "Are there any balance sheet anomalies I should know about?",
            "What is the overall risk rating and key risk drivers?",
        ],
    },
    {
        label: "Valuation",
        icon: DollarSign,
        questions: [
            "What enterprise value does the DCF model produce?",
            "What WACC and terminal growth rate assumptions were used?",
            "How do the EV/EBITDA and EV/Revenue multiples look?",
        ],
    },
    {
        label: "Due Diligence",
        icon: BookOpen,
        questions: [
            "What questions should I ask management before closing?",
            "Summarise the key findings from the full financial review.",
            "What are the Net Working Capital risks going into close?",
        ],
    },
];

// Context-aware follow-up questions based on the last answer
function deriveFollowUps(latestContent: string): string[] {
    const c = latestContent.toLowerCase();
    if (c.includes("ebitda") || c.includes("adjustment") || c.includes("qoe")) {
        return [
            "Which adjustments had the largest dollar impact?",
            "How does adjusted EBITDA margin compare to industry benchmarks?",
            "Are there any owner-related expenses that should be normalised?",
        ];
    }
    if (c.includes("red flag") || c.includes("risk") || c.includes("anomaly")) {
        return [
            "What's the most critical risk to the deal thesis?",
            "Are there any off-balance-sheet liabilities flagged?",
            "What mitigations can we put in the purchase agreement?",
        ];
    }
    if (c.includes("dcf") || c.includes("enterprise value") || c.includes("wacc") || c.includes("valuation")) {
        return [
            "How sensitive is enterprise value to a 1% change in WACC?",
            "What does the equity value look like after netting out debt?",
            "How does this valuation compare to comparable transactions?",
        ];
    }
    if (c.includes("working capital") || c.includes("nwc") || c.includes("ccc") || c.includes("dso")) {
        return [
            "What NWC peg would you recommend for the purchase agreement?",
            "Are DSO trends improving or deteriorating over time?",
            "What's driving the current ratio figure?",
        ];
    }
    if (c.includes("revenue") || c.includes("recurring") || c.includes("customer")) {
        return [
            "What is the customer concentration risk?",
            "Is there any revenue from related-party transactions?",
            "How has revenue trended over the historical periods?",
        ];
    }
    if (c.includes("management") || c.includes("question")) {
        return [
            "What should we ask about the seller's representations and warranties?",
            "Are there any pending legal matters or contingent liabilities?",
            "What key-man risk exists in the management team?",
        ];
    }
    // Generic fallback
    return [
        "What are the biggest risks to the deal?",
        "Summarise the earnings quality findings.",
        "What does the DCF valuation show?",
    ];
}

// ─── Markdown renderer ────────────────────────────────────────────────────────
function renderContent(text: string) {
    const lines = text.split("\n");
    const elements: React.ReactNode[] = [];

    lines.forEach((line, i) => {
        if (line.startsWith("### ")) {
            elements.push(<h3 key={i} className="text-xs font-bold text-slate-900 uppercase tracking-wider mt-4 mb-1.5 border-b border-slate-100 pb-1">{line.slice(4)}</h3>);
        } else if (line.startsWith("## ")) {
            elements.push(<h2 key={i} className="text-sm font-bold text-slate-900 mt-4 mb-1">{line.slice(3)}</h2>);
        } else if (line.startsWith("- ") || line.startsWith("• ")) {
            elements.push(
                <div key={i} className="flex gap-2 my-0.5">
                    <span className="text-blue-400 mt-1.5 shrink-0">▸</span>
                    <p className="text-sm text-slate-700 leading-relaxed">{inlineBold(line.slice(2))}</p>
                </div>
            );
        } else if (/^\d+\.\s/.test(line)) {
            const num = line.match(/^(\d+)\./)?.[1];
            elements.push(
                <div key={i} className="flex gap-2 my-0.5">
                    <span className="text-xs font-bold text-blue-500 bg-blue-50 rounded-full h-5 w-5 flex items-center justify-center shrink-0 mt-0.5">{num}</span>
                    <p className="text-sm text-slate-700 leading-relaxed">{inlineBold(line.replace(/^\d+\.\s/, ""))}</p>
                </div>
            );
        } else if (line === "---") {
            elements.push(<hr key={i} className="my-3 border-slate-100" />);
        } else if (line.trim() === "") {
            elements.push(<div key={i} className="h-1.5" />);
        } else {
            elements.push(<p key={i} className="text-sm text-slate-700 leading-relaxed">{inlineBold(line)}</p>);
        }
    });

    return elements;
}

function inlineBold(text: string): React.ReactNode {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((p, i) =>
        p.startsWith("**") && p.endsWith("**")
            ? <strong key={i} className="font-semibold text-slate-900">{p.slice(2, -2)}</strong>
            : p
    );
}

// ─── Source chip ──────────────────────────────────────────────────────────────
function SourceChip({ source }: { source: { filename: string; relevance_score: number; chunk_text: string } }) {
    const [open, setOpen] = useState(false);
    const pct = Math.round(source.relevance_score * 100);
    const color = pct >= 70 ? "bg-emerald-50 border-emerald-200 text-emerald-700"
        : pct >= 40 ? "bg-amber-50 border-amber-200 text-amber-700"
            : "bg-slate-50 border-slate-200 text-slate-500";

    return (
        <div className={`border rounded-lg text-xs overflow-hidden ${color}`}>
            <button onClick={() => setOpen(!open)} className="w-full flex items-center gap-2 px-3 py-1.5 text-left hover:opacity-80 transition-opacity">
                <FileText className="h-3 w-3 shrink-0" />
                <span className="font-medium truncate flex-1">{source.filename}</span>
                <span className="font-bold shrink-0">{pct}%</span>
                {open ? <ChevronUp className="h-3 w-3 shrink-0" /> : <ChevronDown className="h-3 w-3 shrink-0" />}
            </button>
            {open && (
                <div className="px-3 pb-2 pt-1 border-t border-current/10">
                    <p className="text-xs leading-relaxed opacity-75 line-clamp-4">{source.chunk_text}</p>
                </div>
            )}
        </div>
    );
}

// ─── Follow-up pills ──────────────────────────────────────────────────────────
function FollowUpPills({ questions, onAsk }: { questions: string[]; onAsk: (q: string) => void }) {
    return (
        <div className="mt-3 pt-3 border-t border-slate-100">
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Zap className="h-3 w-3" /> Follow-up questions
            </p>
            <div className="flex flex-col gap-1.5">
                {questions.map((q) => (
                    <button
                        key={q}
                        onClick={() => onAsk(q)}
                        className="flex items-center gap-2 text-left text-xs text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 hover:border-blue-300 px-3 py-2 rounded-lg transition-all group"
                    >
                        <ArrowRight className="h-3 w-3 shrink-0 text-blue-400 group-hover:translate-x-0.5 transition-transform" />
                        {q}
                    </button>
                ))}
            </div>
        </div>
    );
}

// ─── Message bubble ───────────────────────────────────────────────────────────
function MessageBubble({
    msg, isLatest, onAsk,
}: { msg: ChatMessage; isLatest: boolean; onAsk: (q: string) => void }) {
    const isUser = msg.role === "user";
    const time = new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const followUps = isLatest && !isUser ? deriveFollowUps(msg.content) : null;

    if (isUser) {
        return (
            <div className="flex justify-end gap-2.5 group">
                <div className="flex flex-col items-end gap-1 max-w-[75%]">
                    <div className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
                        <p className="text-sm leading-relaxed">{msg.content}</p>
                    </div>
                    <span className="text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">{time}</span>
                </div>
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shrink-0 mt-1 shadow-sm">
                    <User className="h-4 w-4 text-white" />
                </div>
            </div>
        );
    }

    return (
        <div className="flex justify-start gap-2.5 group">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-slate-800 to-slate-950 flex items-center justify-center shrink-0 mt-1 shadow-sm">
                <Bot className="h-4 w-4 text-white" />
            </div>
            <div className="flex flex-col gap-1 max-w-[84%]">
                <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3.5 shadow-sm">
                    <div className="space-y-0.5">{renderContent(msg.content)}</div>

                    {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-slate-100 space-y-1.5">
                            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                                <FileText className="h-3 w-3" /> Source Documents
                            </p>
                            {msg.sources.map((s, i) => <SourceChip key={i} source={s} />)}
                        </div>
                    )}

                    {followUps && <FollowUpPills questions={followUps} onAsk={onAsk} />}
                </div>
                <span className="text-[10px] text-slate-400 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">{time}</span>
            </div>
        </div>
    );
}

// ─── Typing indicator ─────────────────────────────────────────────────────────
function TypingIndicator() {
    return (
        <div className="flex justify-start gap-2.5">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-slate-800 to-slate-950 flex items-center justify-center shrink-0">
                <Bot className="h-4 w-4 text-white" />
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                <div className="flex items-center gap-1.5">
                    {[0, 180, 360].map((d) => (
                        <div key={d} className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: `${d}ms` }} />
                    ))}
                </div>
            </div>
        </div>
    );
}

// ─── Main component ───────────────────────────────────────────────────────────
interface Props { dealId: number; }

export default function ChatPanel({ dealId }: Props) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState("");
    const [sending, setSending] = useState(false);
    const [selectedGroup, setSelectedGroup] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const scrollToBottom = useCallback(() => {
        setTimeout(() => {
            scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
        }, 60);
    }, []);

    useEffect(() => {
        getChatHistory(dealId)
            .then(({ messages: m }) => setMessages(m))
            .catch(() => { });
    }, [dealId]);

    useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);

    const handleSend = async (text: string) => {
        const trimmed = text.trim();
        if (!trimmed || sending) return;
        setInput("");
        setError(null);
        setSending(true);
        if (textareaRef.current) { textareaRef.current.style.height = "auto"; }

        const userMsg: ChatMessage = {
            id: Date.now(), role: "user", content: trimmed,
            sources: null, created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMsg]);
        scrollToBottom();

        try {
            const resp = await sendChatMessage(dealId, trimmed);
            setMessages((prev) => [...prev, resp]);
        } catch {
            setError("Could not reach the AI service. Make sure the backend is running.");
            setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
        } finally {
            setSending(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(input); }
    };

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInput(e.target.value);
        e.target.style.height = "auto";
        e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
    };

    const handleClear = async () => {
        await clearChat(dealId).catch(() => { });
        setMessages([]);
        setError(null);
    };

    const group = SUGGESTION_GROUPS[selectedGroup];
    const isEmpty = messages.length === 0 && !sending;

    return (
        <div className="flex flex-col h-[calc(100vh-260px)] min-h-[560px] bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">

            {/* ─── Header ─── */}
            <div className="flex items-center justify-between px-5 py-3.5 bg-slate-950 text-white shrink-0">
                <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-900/40">
                        <Sparkles className="h-4 w-4 text-white" />
                    </div>
                    <div>
                        <h2 className="text-sm font-bold tracking-tight">TAM AI Analyst</h2>
                        <p className="text-[11px] text-slate-400">Powered by Claude · Anthropic · RAG over your documents</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {messages.length > 0 && (
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                            <MessageSquare className="h-3 w-3" /> {messages.length}
                        </span>
                    )}
                    <button
                        onClick={handleClear}
                        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors px-2.5 py-1.5 rounded-lg hover:bg-white/10"
                    >
                        <RotateCcw className="h-3 w-3" /> Clear
                    </button>
                </div>
            </div>

            {/* ─── Messages ─── */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-5 space-y-5 bg-slate-50">

                {/* Empty state */}
                {isEmpty && (
                    <div className="flex flex-col items-center justify-center h-full gap-6 text-center py-4">
                        <div>
                            <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-slate-800 to-slate-950 flex items-center justify-center mx-auto mb-4 shadow-lg">
                                <Bot className="h-7 w-7 text-white" />
                            </div>
                            <h3 className="text-base font-bold text-slate-900">Ask me about this deal</h3>
                            <p className="text-sm text-slate-500 mt-1 max-w-xs mx-auto">
                                I have full access to the financial analysis, QoE findings, red flags, DCF model, and all uploaded documents.
                            </p>
                        </div>

                        {/* Category tabs */}
                        <div className="w-full max-w-md">
                            <div className="flex gap-2 justify-center mb-3 flex-wrap">
                                {SUGGESTION_GROUPS.map((g, i) => {
                                    const Icon = g.icon;
                                    return (
                                        <button
                                            key={i}
                                            onClick={() => setSelectedGroup(i)}
                                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${selectedGroup === i
                                                ? "bg-slate-900 text-white shadow-md"
                                                : "bg-white border border-slate-200 text-slate-600 hover:border-slate-300 hover:text-slate-900"
                                                }`}
                                        >
                                            <Icon className="h-3 w-3" />
                                            {g.label}
                                        </button>
                                    );
                                })}
                            </div>

                            <div className="space-y-2">
                                {group.questions.map((q) => (
                                    <button
                                        key={q}
                                        onClick={() => handleSend(q)}
                                        className="w-full text-left text-sm text-slate-700 bg-white hover:bg-blue-50 border border-slate-200 hover:border-blue-300 hover:text-blue-800 px-4 py-3 rounded-xl transition-all flex items-center gap-3 group shadow-sm"
                                    >
                                        <Zap className="h-3.5 w-3.5 text-slate-300 group-hover:text-blue-500 shrink-0 transition-colors" />
                                        {q}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Message list */}
                {messages.map((msg, idx) => (
                    <MessageBubble
                        key={msg.id}
                        msg={msg}
                        isLatest={idx === messages.length - 1}
                        onAsk={handleSend}
                    />
                ))}

                {sending && <TypingIndicator />}
            </div>

            {/* ─── Error ─── */}
            {error && (
                <div className="mx-4 mb-3 flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg px-4 py-2.5 shrink-0">
                    <HelpCircle className="h-3.5 w-3.5 shrink-0" />
                    {error}
                </div>
            )}

            {/* ─── Input bar ─── */}
            <div className="px-4 pb-4 pt-3 bg-white border-t border-slate-100 shrink-0">
                <div className="flex items-end gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-400 transition-all shadow-sm">
                    <textarea
                        ref={textareaRef}
                        value={input}
                        onChange={handleInput}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask anything about this deal… (Shift+Enter for new line)"
                        rows={1}
                        disabled={sending}
                        className="flex-1 bg-transparent text-sm text-slate-800 placeholder:text-slate-400 resize-none outline-none min-h-[32px] max-h-[120px] leading-relaxed py-0"
                    />
                    <button
                        onClick={() => handleSend(input)}
                        disabled={sending || !input.trim()}
                        className="shrink-0 h-8 w-8 flex items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 text-white shadow-sm hover:shadow-md disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                    >
                        <Send className="h-3.5 w-3.5" />
                    </button>
                </div>
                <p className="text-[10px] text-slate-400 mt-1.5 text-center">
                    AI responses are grounded in your uploaded documents and TAM&rsquo;s financial analysis.
                </p>
            </div>
        </div>
    );
}
