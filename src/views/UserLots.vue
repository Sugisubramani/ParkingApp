<template>
  <div class="dashboard-wrapper">
    <UserNavbar :username="user?.username || 'User'" />

    <div class="scroll-area">
      <div v-if="loading" class="loader-container">
        <div class="spinner-border text-primary" role="status"></div>
        <p class="loader-text">Loading parking lots…</p>
      </div>

      <div v-else-if="error" class="alert alert-danger text-center mt-4">{{ error }}</div>

      <section v-else>
        <h4 class="section-title">Available Parking Lots</h4>
        <div class="lot-grid row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
          <div v-for="lot in lots" :key="lot.id" class="col">
            <div class="card lot-card h-100">
              <div class="card-body d-flex flex-column justify-content-between">
                <div>
                  <h5 class="lot-name">{{ lot.name }}</h5>
                  <p class="lot-location mb-2">{{ lot.location }}</p>
                  <div><strong>Total:</strong> {{ lot.total_spots }}</div>
                  <div><strong>Available:</strong> {{ lot.available_spots }}</div>
                </div>
                <button
                  class="btn btn-primary mt-3"
                  :disabled="lot.available_spots === 0"
                  @click="reserveSpot(lot.id)"
                >
                  Reserve
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import UserNavbar from '../components/UserNavbar.vue'

export default {
  name: 'UserLots',
  components: { UserNavbar },
  data() {
    return {
      lots: [],
      user: null,
      loading: true,
      error: ''
    }
  },
  methods: {
    async fetchData() {
      const token = localStorage.getItem('token')
      try {
        const userRes = await axios.get('http://localhost:5000/user/dashboard', {
          headers: { Authorization: `Bearer ${token}` }
        })
        this.user = userRes.data

        const lotsRes = await axios.get('http://localhost:5000/user/lots', {
          headers: { Authorization: `Bearer ${token}` }
        })
        this.lots = lotsRes.data
      } catch (err) {
        console.error(err)
        if (err.response?.status === 401) {
          this.error = 'Session expired. Please log in again.'
          localStorage.clear()
          this.$router.push('/login')
        } else {
          this.error = 'Failed to load parking lots.'
        }
      } finally {
        this.loading = false
      }
    },
    async reserveSpot(lotId) {
      try {
        await axios.post(
          'http://localhost:5000/user/reserve',
          { lot_id: lotId },
          { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
        )
        this.fetchData()
      } catch (err) {
        console.error(err)
        alert(err.response?.data?.msg || 'Failed to reserve spot.')
      }
    }
  },
  mounted() {
    this.fetchData()
  }
}
</script>

<style scoped>
.dashboard-wrapper {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg);
  color: var(--text);
}

.scroll-area {
  flex-grow: 1;
  overflow-y: auto;
  padding: 2rem 1rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: var(--primary);
  text-align: center;
}

/* Loader */
.loader-container {
  text-align: center;
  margin-top: 4rem;
}
.loader-text {
  margin-top: .75rem;
  color: var(--secondary);
}

/* Lot Cards */
.lot-grid {
  margin-top: 1rem;
}
.lot-card {
  background: var(--card-bg);
  border: none;
  border-radius: .5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, .06);
  transition: transform .2s ease, box-shadow .2s ease;
}
.lot-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, .12);
}
.lot-name {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: .25rem;
}
.lot-location {
  font-size: .95rem;
  color: var(--secondary);
}
</style>
