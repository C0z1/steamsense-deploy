'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import {
  Sparkles, Zap, TrendingDown, ChevronRight,
  Brain, Tag, RefreshCw, Star, User
} from 'lucide-react'
import { getRecommendations } from '@/lib/api'
import { formatPrice, steamImageUrl } from '@/lib/utils'

// ── Genre color map ───────────────────────────────────────────────────────────
const GENRE_COLORS: Record<string, string> = {
  RPG:        'bg-purple-500/15 text-purple-400 border-purple-500/20',
  FPS:        'bg-red-500/15 text-red-400 border-red-500/20',
  Strategy:   'bg-blue-500/15 text-blue-400 border-blue-500/20',
  Action:     'bg-orange-500/15 text-orange-400 border-orange-500/20',
  Survival:   'bg-green-500/15 text-green-400 border-green-500/20',
  Racing:     'bg-yellow-500/15 text-yellow-400 border-yellow-500/20',
  Simulation: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/20',
  Horror:     'bg-rose-500/15 text-rose-400 border-rose-500/20',
  Sports:     'bg-lime-500/15 text-lime-400 border-lime-500/20',
  Indie:      'bg-pink-500/15 text-pink-400 border-pink-500/20',
  Adventure:  'bg-teal-500/15 text-teal-400 border-teal-500/20',
  MOBA:       'bg-indigo-500/15 text-indigo-400 border-indigo-500/20',
}

const defaultGenreColor = 'bg-steam-muted text-steam-subtle border-steam-subtle/20'

// ── Rec Card ──────────────────────────────────────────────────────────────────
function RecCard({ rec, index }: { rec: any; index: number }) {
  const img          = steamImageUrl(rec.appid)
  const hasDeal      = (rec.discount_pct ?? 0) > 0
  const isNearLow    = rec.min_price > 0 && rec.current_price > 0
                       && rec.current_price <= rec.min_price * 1.05
  const mlScore      = Math.round(rec.ml_score ?? rec.score ?? 0)
  const finalScore   = Math.round(rec.final_score ?? mlScore)
  const hasAffinity  = rec.matched_genres?.length > 0
  const personalized = rec.personalized

  // Limpiar reason — quitar el prefijo de géneros si ya lo mostramos en badges
  const cleanReason = (rec.reason || '').replace(/^Matches your .+ taste · /, '')

  return (
    <Link
      href={`/game/${rec.id}`}
      className="glass glass-hover rounded-2xl overflow-hidden group block animate-slide-up"
      style={{ animationDelay: `${index * 40}ms`, animationFillMode: 'both' }}
    >
      {/* Image */}
      <div className="relative h-28 bg-steam-muted overflow-hidden">
        {img ? (
          <img
            src={img} alt={rec.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        ) : (
          <div className="absolute inset-0 bg-gradient-to-br from-steam-muted to-steam-card flex items-center justify-center">
            <span className="text-steam-subtle/30 text-3xl font-display font-bold">
              {rec.title?.charAt(0)}
            </span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-steam-card/90 via-transparent to-transparent" />

        {/* Discount badge */}
        {hasDeal && (
          <div className="absolute top-2 right-2 px-2 py-0.5 rounded-lg text-xs font-mono font-bold bg-steam-green/20 border border-steam-green/40 text-steam-green">
            −{rec.discount_pct}%
          </div>
        )}

        {/* ATL badge */}
        {isNearLow && (
          <div className="absolute top-2 left-2 px-2 py-0.5 rounded-lg text-xs font-mono bg-steam-cyan/15 border border-steam-cyan/30 text-steam-cyan flex items-center gap-1">
            <TrendingDown size={9} /> ATL
          </div>
        )}

        {/* Personalized badge */}
        {personalized && hasAffinity && (
          <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-lg text-xs font-mono bg-purple-500/20 border border-purple-500/30 text-purple-400 flex items-center gap-1">
            <User size={9} /> For you
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-3 space-y-2">
        <h3 className="text-steam-text text-sm font-semibold leading-snug line-clamp-1 group-hover:text-steam-cyan transition-colors">
          {rec.title}
        </h3>

        {/* Price */}
        {rec.current_price > 0 && (
          <div className="flex items-center gap-2">
            <span className={`font-mono font-bold text-sm ${hasDeal ? 'text-steam-green' : 'text-steam-text'}`}>
              {formatPrice(rec.current_price)}
            </span>
            {rec.min_price > 0 && rec.min_price < rec.current_price && (
              <span className="text-steam-subtle/50 text-xs font-mono">
                ATL {formatPrice(rec.min_price)}
              </span>
            )}
          </div>
        )}

        {/* Genre badges */}
        {rec.matched_genres?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {rec.matched_genres.slice(0, 3).map((g: string) => (
              <span
                key={g}
                className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${GENRE_COLORS[g] ?? defaultGenreColor}`}
              >
                {g}
              </span>
            ))}
          </div>
        )}

        {/* Score bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-steam-subtle font-mono flex items-center gap-1">
              <Brain size={9} />
              {personalized ? 'Match score' : 'ML score'}
            </span>
            <span className={`font-mono font-semibold ${
              finalScore >= 70 ? 'text-steam-green' :
              finalScore >= 50 ? 'text-steam-amber' : 'text-steam-red'
            }`}>
              {finalScore}
            </span>
          </div>
          <div className="h-1 bg-steam-muted rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                finalScore >= 70 ? 'bg-steam-green' :
                finalScore >= 50 ? 'bg-steam-amber' : 'bg-steam-red'
              }`}
              style={{ width: `${Math.min(finalScore, 100)}%` }}
            />
          </div>
        </div>

        {/* Reason */}
        {cleanReason && (
          <p className="text-steam-subtle/70 text-[10px] leading-relaxed line-clamp-2">
            {cleanReason}
          </p>
        )}
      </div>
    </Link>
  )
}

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyRecs() {
  return (
    <div className="space-y-4">
      <div className="text-center py-12 space-y-3">
        <Sparkles size={32} className="text-steam-subtle/40 mx-auto" />
        <p className="text-steam-subtle text-sm max-w-sm mx-auto">
          No recommendations yet. Sync your library and populate the database so the model can generate BUY signals.
        </p>
      </div>
      <div className="glass rounded-xl px-5 py-4 border border-steam-cyan/20">
        <p className="text-steam-cyan text-sm font-semibold flex items-center gap-2 mb-3">
          <Zap size={13} /> How to get recommendations
        </p>
        <ol className="text-steam-subtle text-xs space-y-2 list-decimal list-inside leading-relaxed">
          <li>Go to <span className="text-steam-text">Library</span> tab → click <span className="text-steam-text">"Setup Guide"</span></li>
          <li>Run <span className="text-steam-text">"Run Sync"</span> to download price history</li>
          <li>Run <span className="text-steam-text">"Generate"</span> to create BUY/WAIT predictions</li>
          <li>Sync your library so the model learns your taste</li>
          <li>Come back here — you'll see personalized recommendations</li>
        </ol>
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export default function RecsTab({ token }: { token: string }) {
  const [recs, setRecs]         = useState<any[]>([])
  const [loading, setLoading]   = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const load = async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true)
    try {
      const d = await getRecommendations(token, 24)
      setRecs(d.recommendations || [])
    } catch { } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => { load() }, [token])

  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="glass rounded-2xl h-56 animate-pulse shimmer" />
        ))}
      </div>
    )
  }

  if (!recs.length) return <EmptyRecs />

  const personalized = recs.some(r => r.personalized && r.matched_genres?.length > 0)
  const genreSet = [...new Set(recs.flatMap(r => r.matched_genres || []))]

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <p className="text-steam-text text-sm">
            {personalized
              ? <>Games tailored to <span className="text-steam-cyan">your playstyle</span> that are worth buying right now.</>
              : <>Games you <span className="text-steam-text font-semibold">don't own</span> that our ML model says are worth buying right now.</>
            }
          </p>
          {personalized && genreSet.length > 0 && (
            <p className="text-steam-subtle text-xs">
              Based on your top genres: {genreSet.slice(0, 4).join(', ')}
            </p>
          )}
        </div>
        <button
          onClick={() => load(true)}
          disabled={refreshing}
          className="flex-shrink-0 flex items-center gap-2 px-3 py-1.5 glass rounded-xl text-xs font-mono text-steam-subtle hover:text-steam-text transition-all disabled:opacity-50"
        >
          <RefreshCw size={11} className={refreshing ? 'animate-spin text-steam-cyan' : ''} />
          Refresh
        </button>
      </div>

      {/* Personalization notice */}
      {personalized && (
        <div className="flex items-center gap-2 px-3 py-2 glass rounded-xl border border-purple-500/20 bg-purple-500/5">
          <User size={13} className="text-purple-400 flex-shrink-0" />
          <p className="text-purple-400 text-xs">
            Personalized based on your playtime — games matching your taste rank higher
          </p>
        </div>
      )}

      {/* Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {recs.map((r, i) => (
          <RecCard key={r.id} rec={r} index={i} />
        ))}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 pt-2 border-t border-steam-muted/30">
        <div className="flex items-center gap-1.5 text-xs text-steam-subtle">
          <Brain size={11} className="text-steam-cyan" />
          ML score = price timing model
        </div>
        {personalized && (
          <div className="flex items-center gap-1.5 text-xs text-steam-subtle">
            <User size={11} className="text-purple-400" />
            Match score = ML + your genre affinity
          </div>
        )}
        <div className="flex items-center gap-1.5 text-xs text-steam-subtle">
          <TrendingDown size={11} className="text-steam-cyan" />
          ATL = at or near all-time low price
        </div>
      </div>
    </div>
  )
}
