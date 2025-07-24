<template>
  <!-- 1) Loading State -->
  <div v-if="loading" class="loader-container">
    <div class="spinner-border text-primary" role="status"></div>
    <p class="loader-text">Loading summary…</p>
  </div>

  <!-- 2) Error State -->
  <div v-else-if="error" class="alert alert-danger text-center mt-4">
    {{ error }}
  </div>

  <!-- 3) Main Content -->
  <div v-else class="dashboard-wrapper">
    <UserNavbar :username="displayName" />

    <div class="scroll-area">
      <h2 class="section-title mb-4">Monthly Summary</h2>

      <!-- wrap summary + chart side by side -->
      <div class="summary-chart-wrapper">
        <!-- Summary Card -->
        <div class="card shadow-sm p-4 summary-card">
          <p class="mb-2"><strong>Total Reservations:</strong> {{ totalReservations }}</p>
          <p class="mb-2"><strong>Total Hours Parked:</strong> {{ totalHours.toFixed(1) }}</p>
          <p class="mb-2"><strong>Total Amount Spent:</strong> ₹{{ totalCost.toFixed(2) }}</p>
          <p class="mb-0"><strong>Most Frequent Lot:</strong> {{ frequentLot || 'N/A' }}</p>
        </div>

        <!-- Bar Chart -->
        <div class="card shadow-sm p-4 chart-card">
          <h5 class="card-title mb-3">Times Parked by Lot</h5>
          <div class="chart-container">
            <canvas ref="timesChart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import UserNavbar from '../components/UserNavbar.vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'UserSummary',
  components: { UserNavbar },

  data() {
    return {
      user: null,
      dataByLot: [],
      chart: null,
      loading: true,
      error: ''
    }
  },

  computed: {
    displayName() {
      return this.user?.fullname
        || this.user?.username
        || this.user?.email
        || 'User'
    },
    totalReservations() {
      return this.dataByLot.reduce((sum, l) => sum + (l.times_parked||0), 0)
    },
    totalHours() {
      const mins = this.dataByLot.reduce((sum, l) => sum + (l.total_time_minutes||0), 0)
      return mins/60
    },
    totalCost() {
      return this.dataByLot.reduce((sum, l) => sum + (l.total_cost||0), 0)
    },
    frequentLot() {
      if (!this.dataByLot.length) return ''
      return this.dataByLot
        .slice()
        .sort((a,b) => (b.times_parked||0)-(a.times_parked||0))[0]
        .lot_name
    }
  },

  watch: {
    dataByLot(newVal) {
      if (newVal.length) this.$nextTick(this.renderChart)
    }
  },

  methods: {
    renderChart() {
      const canvas = this.$refs.timesChart
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      if (this.chart) {
        this.chart.destroy()
        this.chart = null
      }

      const labels = this.dataByLot.map(l => l.lot_name)
      const data   = this.dataByLot.map(l => l.times_parked)

      this.chart = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets:[{ label:'Times Parked', data, backgroundColor:'#0d6efd' }] },
        options: {
          animation: false,
          responsive: true,
          maintainAspectRatio: false,
          scales: { y:{ beginAtZero:true, ticks:{ precision:0 } } }
        }
      })
    }
  },

  async mounted() {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token')
    if (!token) {
      this.$router.push('/login')
      return
    }

    try {
      const [sumRes, userRes] = await Promise.all([
        axios.get('http://localhost:5000/user/summary', {
          headers:{ Authorization:`Bearer ${token}` }
        }),
        axios.get('http://localhost:5000/user/dashboard', {
          headers:{ Authorization:`Bearer ${token}` }
        })
      ])

      this.dataByLot = Array.isArray(sumRes.data.summary)
        ? sumRes.data.summary
        : Array.isArray(sumRes.data)
          ? sumRes.data
          : []
      this.user = userRes.data

      if (this.dataByLot.length) this.$nextTick(this.renderChart)
    }
    catch(err) {
      console.error(err)
      if (err.response?.status === 401) {
        localStorage.clear()
        this.$router.push('/login')
      } else {
        this.error = 'Failed to load summary.'
      }
    }
    finally {
      this.loading = false
    }
  }
}
</script>

<style scoped>
.dashboard-wrapper {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 1rem;
}
.loader-container {
  text-align: center;
  margin-top: 4rem;
}
.loader-text {
  margin-top: .75rem;
  font-size: .95rem;
  color: #666;
}
.section-title {
  text-align: center;
  color: #0d6efd;
  margin-bottom: 1.5rem;
}

/* new wrapper to align summary + chart */
.summary-chart-wrapper {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  flex-wrap: wrap;
}   

/* summary takes 30% width */
.summary-card {
  flex: 0 0 30%;
  min-width: 250px;
  background: #fff;
  border-radius: .5rem;
  box-shadow: 0 2px 6px rgba(0,0,0,.1);
  padding: 1.25rem;
}

/* chart takes remaining width */
.chart-card {
  flex: 1;
  background: #fff;
  border-radius: .5rem;
  box-shadow: 0 2px 6px rgba(0,0,0,.1);
  padding: 1.25rem;
}

.chart-container {
  position: relative;
  height: 300px;
}
</style>
