<template>
  <div class="mt-4 text-gray-700 text-base">
    <div class="mt-10 text-gray-700 text-base">
      <p class="text-md mx-auto leading-relaxed text-justify">
        The leaderboard displays the performance of various models across different game theory games.
        Select a game to see how models compare. The "Overall" view shows the average score across all games (using Implicit for El Farol Bar and Highest for Sealed-Bid Auction).
      </p>
    </div>

    <!-- Game Buttons -->
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 mb-4 mt-6 max-w-6xl mx-auto">
      <button
        v-for="game in gameList"
        :key="game"
        class="px-4 py-2 border rounded-lg transition-colors duration-200 text-sm font-medium"
        :class="{
          'bg-blue-600 text-white': selectedGame === game,
          'bg-white text-gray-700 border-gray-300 hover:bg-gray-100': selectedGame !== game
        }"
        @click="selectGame(game)"
      >
        {{ game }}
      </button>
    </div>

    <!-- Sub-option Buttons (for El Farol Bar and Sealed-Bid Auction) -->
    <div v-if="hasSubOptions" class="flex flex-wrap justify-center gap-2 mb-4">
      <button
        v-for="option in subOptions"
        :key="option"
        class="px-3 py-1.5 border rounded-lg transition-colors duration-200 text-xs font-medium"
        :class="{
          'bg-green-600 text-white': selectedSubOption === option,
          'bg-white text-gray-600 border-gray-300 hover:bg-gray-100': selectedSubOption !== option
        }"
        @click="selectSubOption(option)"
      >
        {{ option }}
      </button>
    </div>

    <!-- Notes Section -->
    <div class="mt-6 mb-8 text-gray-700 text-base">
      <h2 class="text-3xl font-bold mb-4">📝 Notes</h2>
      <ul class="list-disc list-inside leading-relaxed text-left">
        <li><strong>Scoring Interpretation:</strong> Scores measure how closely a model's decisions align with the <strong>Nash equilibrium</strong> strategy for each game.</li>
        <li><strong>Higher Scores:</strong> Indicate that the model's behavior is closer to the theoretically optimal rational strategy (Nash equilibrium).</li>
        <li><strong>Overall Score:</strong> Represents the average alignment across all games, using Implicit for El Farol Bar and Highest for Sealed-Bid Auction.</li>
        <li><strong>Game Variants:</strong> Games have multiple versions (e.g., El Farol Bar: Implicit/Explicit; Sealed-Bid Auction: Highest/Second) testing different strategic contexts.</li>
        <li>Click on column headers to sort the table by model name or score.</li>
      </ul>
    </div>

    <div class="overflow-x-auto shadow-lg rounded-xl bg-white">
      <table class="min-w-full table-auto border-collapse text-lg">
        <thead>
          <tr class="bg-gradient-to-r from-gray-100 to-gray-200 text-base text-gray-700">
            <th
              class="border px-4 py-3 text-center cursor-pointer select-none hover:bg-gray-300 transition-colors duration-150 group"
              @click="toggleSort('model')"
            >
              <div class="h-4 leading-none invisible">▲</div>
              <div class="font-semibold">Model</div>
              <div
                class="text-xs h-4 leading-none transition-opacity duration-150"
                :class="[
                  sortBy === 'model' ? 'opacity-100' : 'opacity-0 group-hover:opacity-40',
                ]"
              >
                {{ sortOrder === 'asc' ? '▲' : '▼' }}
              </div>
            </th>
            <th
              class="border px-4 py-2 cursor-pointer select-none hover:bg-gray-300 transition-colors duration-150 text-center group whitespace-nowrap"
              @click="toggleSort('score')"
            >
              <div class="h-4 leading-none invisible">▲</div>
              <div class="font-semibold">Score</div>
              <div
                class="text-xs h-4 leading-none transition-opacity duration-150"
                :class="[
                  sortBy === 'score' ? 'opacity-100' : 'opacity-0 group-hover:opacity-40',
                ]"
              >
                {{ sortOrder === 'asc' ? '▲' : '▼' }}
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in sortedRows"
            :key="row.model"
            class="hover:bg-blue-50 transition-colors duration-150"
          >
            <td class="border px-4 py-2 font-medium text-gray-800 whitespace-nowrap text-base">
              {{ row.model }}
            </td>
            <td class="border px-4 py-2 text-center text-gray-700">
              {{ formatCell(row.score) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <h2 class="text-4xl font-bold text-center mt-12 mb-4">BibTeX</h2>
    <div class="relative w-full max-w-4xl mx-auto">
      <button
        @click="copyBib"
        class="absolute top-2 right-0 flex items-center justify-center rounded bg-gray-200 text-gray-700 hover:bg-gray-300 transition"
        style="width: 85px; height: 30px; font-size: 12px;"
      >
        {{ copied ? 'Copied!' : 'Copy' }}
      </button>
      <div
        v-if="copied"
        class="absolute top-2 right-24 px-3 py-1 bg-green-500 text-white text-sm rounded shadow-lg animate-bounce"
      >
        ✓ Copied!
      </div>
      <pre class="w-full bg-gray-100 p-4 border border-gray-300 text-sm font-mono text-left rounded-xl overflow-x-auto"><code ref="bib">@inproceedings{huang2025competing,
  title={Competing large language models in multi-agent gaming environments},
  author={Huang, Jen-tse and Li, Eric John and Lam, Man Ho and Liang, Tian and Wang, Wenxuan and \
    Yuan, Youliang and Jiao, Wenxiang and Wang, Xing and Tu, Zhaopeng and Lyu, Michael},
  booktitle={The Thirteenth International Conference on Learning Representations},
  year={2025}
}</code></pre>
    </div>

    <!-- More Leaderboards Section -->
    <div class="mt-16 mb-8">
      <h2 class="text-4xl font-bold mt-12 mb-4">🤗 More Leaderboards</h2>
      <p class="text-left mb-4">
        Exploring more excellent benchmarks and leaderboards from ARISE Lab:
      </p>
      <ul class="list-disc list-inside leading-relaxed text-left">
        <li>
          <a href="https://cuhk-arise.github.io/PsychoBench/" target="_blank" class="text-blue-600 hover:underline">PsychoBench Leaderboard</a>
          <span class="ml-2 px-2 py-0.5 text-xs font-semibold rounded bg-orange-100 text-orange-700 border border-orange-300">ICLR'24 Oral</span>
        </li>
        <li>
          <a href="https://cuhk-arise.github.io/EmotionBench/" target="_blank" class="text-blue-600 hover:underline">EmotionBench Leaderboard</a>
          <span class="ml-2 px-2 py-0.5 text-xs font-semibold rounded bg-green-100 text-green-700 border border-green-300">NeurIPS'24 Poster</span>
        </li>
        <li>
          <a href="https://cuhk-arise.github.io/CodeCrash/" target="_blank" class="text-blue-600 hover:underline">CodeCrash Leaderboard</a>
          <span class="ml-2 px-2 py-0.5 text-xs font-semibold rounded bg-green-100 text-green-700 border border-green-300">NeurIPS'25 Poster</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const leaderboardData = ref({})
const sortBy = ref('model')
const sortOrder = ref('asc')
const selectedGame = ref('')
const selectedSubOption = ref('')
const copied = ref(false)

// Parse game names and group them
const gameGroups = computed(() => {
  const groups = {}
  Object.keys(leaderboardData.value).forEach(fullName => {
    const match = fullName.match(/^(.+?)\s*\((.+?)\)$/)
    if (match) {
      const [, baseName, subOption] = match
      if (!groups[baseName]) {
        groups[baseName] = []
      }
      groups[baseName].push(subOption)
    } else {
      groups[fullName] = null
    }
  })
  return groups
})

// Calculate overall scores (average of all games with Implicit and Highest)
const overallData = computed(() => {
  const overall = {}
  const gamesToAverage = []

  // Collect all game names to average
  Object.keys(leaderboardData.value).forEach(fullName => {
    const match = fullName.match(/^(.+?)\s*\((.+?)\)$/)
    if (match) {
      const [, baseName, subOption] = match
      // Only include Implicit for El Farol Bar and Highest for Sealed-Bid Auction
      if ((baseName === 'El Farol Bar' && subOption === 'Implicit') ||
          (baseName === 'Sealed-Bid Auction' && subOption === 'Highest')) {
        gamesToAverage.push(fullName)
      }
    } else {
      // Include all other games
      gamesToAverage.push(fullName)
    }
  })

  // Calculate average for each model
  const modelCounts = {}
  gamesToAverage.forEach(gameName => {
    const gameData = leaderboardData.value[gameName]
    Object.entries(gameData).forEach(([model, score]) => {
      if (!overall[model]) {
        overall[model] = 0
        modelCounts[model] = 0
      }
      overall[model] += score
      modelCounts[model]++
    })
  })

  // Divide by count to get average
  Object.keys(overall).forEach(model => {
    overall[model] = overall[model] / modelCounts[model]
  })

  return overall
})

// Get unique list of games (base names) with Overall at the end
const gameList = computed(() => {
  return [...Object.keys(gameGroups.value), 'Overall']
})

// Check if current game has sub-options
const hasSubOptions = computed(() => {
  if (selectedGame.value === 'Overall') return false
  return gameGroups.value[selectedGame.value] !== null
})

// Get sub-options for current game
const subOptions = computed(() => {
  if (selectedGame.value === 'Overall') return []
  return gameGroups.value[selectedGame.value] || []
})

// Get full game name (with sub-option if applicable)
const fullGameName = computed(() => {
  if (hasSubOptions.value && selectedSubOption.value) {
    return `${selectedGame.value} (${selectedSubOption.value})`
  }
  return selectedGame.value
})

// Select game
function selectGame(game) {
  selectedGame.value = game

  // No sub-options for Overall
  if (game === 'Overall') {
    selectedSubOption.value = ''
  }
  // Set default sub-option if game has sub-options
  else if (gameGroups.value[game] !== null) {
    const options = gameGroups.value[game]
    // Default: Implicit for El Farol Bar, Highest for Sealed-Bid Auction
    if (game === 'El Farol Bar') {
      selectedSubOption.value = 'Implicit'
    } else if (game === 'Sealed-Bid Auction') {
      selectedSubOption.value = 'Highest'
    } else {
      selectedSubOption.value = options[0]
    }
  } else {
    selectedSubOption.value = ''
  }

  // Reset sort
  sortBy.value = 'score'
  sortOrder.value = 'desc'
}

// Select sub-option
function selectSubOption(option) {
  selectedSubOption.value = option
  // Reset sort
  sortBy.value = 'score'
  sortOrder.value = 'desc'
}

// Compute row data for each model
const sortedRows = computed(() => {
  if (!selectedGame.value) return []

  // Use overall data if Overall is selected
  const gameData = selectedGame.value === 'Overall'
    ? overallData.value
    : (leaderboardData.value[fullGameName.value] || {})

  const rows = Object.entries(gameData).map(([model, score]) => ({
    model,
    score
  }))

  // Sort by selected column
  return rows.sort((a, b) => {
    if (sortBy.value === 'model') {
      const cmp = a.model.localeCompare(b.model)
      return sortOrder.value === 'asc' ? cmp : -cmp
    }
    const aVal = a.score
    const bVal = b.score
    if (aVal == null) return 1
    if (bVal == null) return -1
    return sortOrder.value === 'asc' ? aVal - bVal : bVal - aVal
  })
})

function toggleSort(column) {
  if (sortBy.value === column) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = column
    sortOrder.value = column === 'score' ? 'desc' : 'asc'
  }
}

function formatCell(val) {
  if (val == null) return '-'
  return typeof val === 'number' ? val.toFixed(2) : val
}

const bib = ref(null)

function copyBib() {
  if (bib.value) {
    navigator.clipboard.writeText(bib.value.textContent)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  }
}

onMounted(async () => {
  try {
    const dataRes = await fetch(`${import.meta.env.BASE_URL}data.json`)
    leaderboardData.value = await dataRes.json()

    // Initialize with Overall selected
    selectGame('Overall')
  } catch (e) {
    console.error('Failed to load data:', e)
  }
})
</script>

<style scoped>
table {
  font-family: Arial, sans-serif;
}
</style>
