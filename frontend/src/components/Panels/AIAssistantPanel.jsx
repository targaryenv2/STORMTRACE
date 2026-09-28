import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Bot, 
  Send, 
  Sparkles, 
  X, 
  MapPin, 
  Zap, 
  Clock, 
  HelpCircle, 
  ShieldAlert, 
  Layers, 
  Activity, 
  ArrowRight,
  Info
} from 'lucide-react';
import { processUserMessage } from '../../services/assistantService';
import TooltipHelper from '../Common/TooltipHelper';

export default function AIAssistantPanel({
  isOpen,
  onClose,
  onExecuteMapAction,
  selectedCellId
}) {
  const { t } = useTranslation();

  const starterPrompts = [
    'Is there a thunderstorm in Tamil Nadu?',
    'Show me the storm in Brazil',
    'Is there a thunderstorm in Dubai?',
    t('assistant.promptWorst'),
    t('assistant.promptChennai'),
    t('assistant.promptRed'),
    t('assistant.promptDbz'),
    t('assistant.promptHour')
  ];

  const [messages, setMessages] = useState([
    {
      id: 'init-1',
      sender: 'bot',
      text: t('assistant.welcomeMessage'),
      disclaimer: t('common.disclaimer'),
      chips: [],
      card: null
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputValue;
    if (!text.trim() || isProcessing) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: text.trim()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsProcessing(true);

    try {
      const response = await processUserMessage(text, { selectedCellId });
      
      // Execute any triggered map actions
      if (response.actions && response.actions.length > 0 && onExecuteMapAction) {
        response.actions.forEach(action => {
          onExecuteMapAction(action);
        });
      }

      const botMsg = {
        id: `bot-${Date.now()}`,
        sender: 'bot',
        text: response.text,
        chips: response.actions?.map(a => a.chipText).filter(Boolean) || [],
        card: response.card
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error('Assistant error:', err);
      setMessages(prev => [
        ...prev,
        {
          id: `bot-err-${Date.now()}`,
          sender: 'bot',
          text: "I couldn't retrieve the requested data. Please try asking again or select a storm cell on the map.",
          chips: [],
          card: null
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="flex flex-col h-full bg-white border-l border-slate-200 shadow-lg text-slate-800 select-none animate-in fade-in duration-150">
      {/* 1. Header */}
      <div className="p-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center shadow-sm">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <h3 className="text-xs font-bold text-slate-900">{t('assistant.title')}</h3>
              <span className="px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-[9px] font-mono font-bold">
                {t('assistant.grounded')}
              </span>
            </div>
            <p className="text-[10px] text-slate-500">{t('assistant.subtitle')}</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
          title="Close Assistant"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* 2. Offline Mode & Safety Notice Banner */}
      <div className="px-3 py-1.5 bg-blue-50/70 border-b border-blue-100 text-[10px] text-blue-800 flex items-center justify-between">
        <span className="flex items-center space-x-1">
          <Sparkles className="w-3 h-3 text-blue-600" />
          <span>{t('assistant.modeNotice')}</span>
        </span>
      </div>

      {/* 3. Messages Chat Flow */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-3.5 custom-scrollbar text-xs">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1.5`}
            >
              <div
                className={`max-w-[88%] p-3 rounded-2xl text-xs leading-relaxed ${
                  isUser
                    ? 'bg-blue-600 text-white rounded-br-xs shadow-sm font-medium'
                    : 'bg-slate-50 border border-slate-200/90 text-slate-800 rounded-bl-xs shadow-sm'
                }`}
              >
                <p>{msg.text}</p>

                {/* Structured Data Card Render */}
                {msg.card && msg.card.type === 'cell' && (
                  <div className="mt-2.5 p-2.5 bg-white border border-slate-200 rounded-xl space-y-1.5 shadow-sm text-slate-800">
                    <div className="flex items-center justify-between font-bold text-xs pb-1 border-b border-slate-100">
                      <span className="text-blue-700">{msg.card.data.cell_id}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] ${
                        msg.card.data.warning_level === 'RED' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {msg.card.data.warning_level} Threat
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-1.5 text-[11px] pt-1">
                      <div>Max dBZ: <strong className="font-semibold">{msg.card.data.max_dbz}</strong></div>
                      <div>Severity: <strong className="font-semibold">{msg.card.data.severity_score}/100</strong></div>
                      <div>Speed: <strong className="font-semibold">{msg.card.data.speed_kmh} km/h</strong></div>
                      <div>Heading: <strong className="font-semibold">{msg.card.data.compass} ({msg.card.data.direction_deg}°)</strong></div>
                    </div>
                  </div>
                )}

                {msg.card && msg.card.type === 'coverage' && (
                  <div className="mt-2.5 p-2.5 bg-amber-50 border border-amber-200 rounded-xl space-y-1 text-amber-900 shadow-sm">
                    <div className="font-bold text-xs flex items-center space-x-1">
                      <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                      <span>{msg.card.data.region} ({msg.card.data.status})</span>
                    </div>
                    <p className="text-[11px] text-amber-800">{msg.card.data.details}</p>
                  </div>
                )}

                {msg.card && msg.card.type === 'glossary' && (
                  <div className="mt-2.5 p-2.5 bg-white border border-slate-200 rounded-xl space-y-1 text-slate-800 shadow-sm">
                    <div className="font-bold text-xs text-blue-700">{msg.card.data.term}</div>
                    <p className="text-[11px] text-slate-600">{msg.card.data.definition}</p>
                  </div>
                )}
              </div>

              {/* Map Action Chips */}
              {msg.chips && msg.chips.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-0.5">
                  {msg.chips.map((chip, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center px-2 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-semibold"
                    >
                      {chip}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {isProcessing && (
          <div className="flex items-center space-x-2 text-slate-400 text-xs py-1">
            <div className="w-2 h-2 rounded-full bg-blue-600 animate-bounce" />
            <div className="w-2 h-2 rounded-full bg-blue-600 animate-bounce delay-100" />
            <div className="w-2 h-2 rounded-full bg-blue-600 animate-bounce delay-200" />
            <span className="text-[11px] font-medium text-slate-500">{t('assistant.retrieving')}</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 4. Suggested Starter Prompts */}
      <div className="p-2.5 border-t border-slate-100 bg-slate-50/50 space-y-1.5">
        <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">{t('assistant.suggestedQuestions')}</div>
        <div className="flex flex-wrap gap-1.5 max-h-20 overflow-y-auto custom-scrollbar">
          {starterPrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(prompt)}
              className="text-[10px] font-medium px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:border-blue-300 hover:text-blue-700 text-slate-600 transition shadow-xs"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* 5. Input Bar */}
      <div className="p-3 border-t border-slate-200 bg-white">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            placeholder={t('assistant.inputPlaceholder')}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isProcessing}
            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 placeholder-slate-400 outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isProcessing}
            className="p-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white transition disabled:opacity-40 shadow-sm"
            title="Send"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
}
