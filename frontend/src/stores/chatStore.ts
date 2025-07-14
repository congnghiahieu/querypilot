import { create } from 'zustand';

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface ChatStore {
  chatHistory: ChatSession[];
  setChatHistory: (history: ChatSession[]) => void;
  addChat: (chat: ChatSession) => void;
  removeChat: (chatId: string) => void;
  updateChat: (chatId: string, updates: Partial<ChatSession>) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  chatHistory: [],
  setChatHistory: (history) => set({ chatHistory: history }),
  addChat: (chat) =>
    set((state) => ({
      chatHistory: [chat, ...state.chatHistory],
    })),
  removeChat: (chatId) =>
    set((state) => ({
      chatHistory: state.chatHistory.filter((chat) => chat.id !== chatId),
    })),
  updateChat: (chatId, updates) =>
    set((state) => ({
      chatHistory: state.chatHistory.map((chat) =>
        chat.id === chatId ? { ...chat, ...updates } : chat,
      ),
    })),
}));
