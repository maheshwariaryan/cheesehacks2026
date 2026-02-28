"use client";
import { use } from "react";
import ChatPanel from "@/components/chat/chat-panel";

export default function ChatPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    return (
        <div className="w-full">
            <ChatPanel dealId={parseInt(id)} />
        </div>
    );
}
