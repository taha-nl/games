import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api, ApiError } from '@/api/client'

interface Card { id: number; name: string; icon: string; description: string; cost_coins: number; card_type: string }
interface ShopData { cards: Card[]; owned: Record<number, number>; team_coins: number }

export default function CardShop() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery<ShopData>({
    queryKey: ['cards-shop'],
    queryFn: () => api.get('/cards/shop'),
  })

  const buy = useMutation({
    mutationFn: (cardId: number) => api.post<{ message: string }>(`/cards/buy/${cardId}`),
    onSuccess: (r: { message: string }) => {
      toast.success(r.message)
      qc.invalidateQueries({ queryKey: ['cards-shop'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: (e: Error) => toast.error(e instanceof ApiError ? e.message : e.message),
  })

  if (isLoading || !data) {
    return <div className="flex items-center justify-center min-h-[60vh]"><div className="text-neon-blue animate-pulse">🃏 Loading shop...</div></div>
  }

  const { cards, owned, team_coins } = data

  const typeLabel: Record<string, string> = {
    double_points: '⚡ Double Points',
    freeze_opponent: '❄️ Freeze Opponent',
    hint: '💡 Hint',
    bug_detector: '🐛 Bug Detector',
    extra_time: '⏰ Extra Time',
    skip_challenge: '⏭️ Skip Challenge',
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-black text-white">🃏 Card Shop</h1>
          <p className="text-gray-400 mt-1">Power-up cards to gain an edge in the competition</p>
        </div>
        <div className="glass rounded-full px-5 py-2 flex items-center gap-2">
          <span>🪙</span>
          <span className="font-black text-amber-300 text-xl">{team_coins}</span>
          <span className="text-gray-400 text-sm">coins</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map(card => {
          const qty = owned[card.id] ?? 0
          const canAfford = team_coins >= card.cost_coins
          return (
            <div key={card.id} className="glass rounded-2xl p-5 border border-white/10 flex flex-col">
              <div className="text-5xl mb-3 text-center">{card.icon}</div>
              <h3 className="font-bold text-white text-lg text-center mb-1">{card.name}</h3>
              <div className="text-center mb-3">
                <span className="text-xs text-neon-purple bg-neon-purple/10 px-2 py-0.5 rounded-full">
                  {typeLabel[card.card_type] ?? card.card_type}
                </span>
              </div>
              <p className="text-gray-400 text-sm text-center flex-1">{card.description}</p>
              <div className="mt-4 pt-4 border-t border-white/10">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-amber-300 font-bold">🪙 {card.cost_coins}</span>
                  {qty > 0 && <span className="text-xs bg-space-600 px-2 py-0.5 rounded-full text-gray-300">Owned: {qty}</span>}
                </div>
                <button
                  onClick={() => buy.mutate(card.id)}
                  disabled={!canAfford || buy.isPending}
                  className={`w-full font-bold py-2.5 rounded-xl transition text-sm ${canAfford ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white' : 'bg-space-600 text-gray-500 cursor-not-allowed'}`}
                >
                  {canAfford ? '🛒 Buy Card' : '🔒 Not Enough Coins'}
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
