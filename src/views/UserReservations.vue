<template>
  <div class="dashboard-wrapper">
    <UserNavbar :username="user?.username || 'User'" />

    <div class="scroll-area">
      <div v-if="loading" class="loader-container">
        <div class="spinner-border text-primary" role="status"></div>
        <p class="loader-text">Loading reservations…</p>
      </div>

      <div v-else-if="error" class="alert alert-danger text-center mt-4">
        {{ error }}
      </div>

      <section v-else>
        <h2 class="section-title">Your Reservations</h2>

        <div v-if="user.reservations?.length" class="cards-grid">
          <div
            v-for="r in user.reservations"
            :key="r.reservation_id"
            class="reservation-card"
          >
            <div class="card-header">
              <div class="header-text">
                <h5 class="lot-name">{{ r.lot_name }}</h5>
                <small class="lot-address">{{ r.lot_address }}</small>
              </div>
              <button
                class="btn btn-sm btn-warning"
                @click="releaseSpot(r.reservation_id)"
              >
                Release
              </button>
            </div>
            <div class="card-body">
              <div class="info"><strong>Spot:</strong> #{{ r.spot_number }}</div>
              <div class="info"><strong>Vehicle:</strong> {{ r.vehicle_number }}</div>
              <div class="info"><strong>Start:</strong> {{ formatDate(r.start_time) }}</div>
              <div class="info">
                <strong>End:</strong>
                {{ r.end_time ? formatDate(r.end_time) : 'Ongoing' }}
              </div>
            </div>
          </div>
        </div>

        <p v-else class="no-reservations">
          You have no active reservations.
        </p>
      </section>
    </div>

    <!-- Release Modal -->
    <div
      class="modal fade"
      tabindex="-1"
      :class="{ show: showReleaseModal }"
      style="display: block;"
      v-if="showReleaseModal"
    >
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Release Reservation</h5>
            <button type="button" class="btn-close" @click="showReleaseModal = false"></button>
          </div>
          <div class="modal-body">
            <ul class="list-group list-group-flush">
              <li class="list-group-item">
                <strong>Lot:</strong> {{ activeReservation.lot_name }}
              </li>
              <li class="list-group-item">
                <strong>Spot:</strong> #{{ activeReservation.spot_number }}
              </li>
              <li class="list-group-item">
                <strong>Vehicle:</strong> {{ activeReservation.vehicle_number }}
              </li>
              <li class="list-group-item">
                <strong>Start Time:</strong> {{ formatDate(activeReservation.start_time) }}
              </li>
              <li class="list-group-item">
                <strong>Release Time:</strong> {{ formatDate(now) }}
              </li>
              <li class="list-group-item">
                <strong>Estimated Cost:</strong> ₹{{ estimatedCost }}
              </li>
            </ul>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showReleaseModal = false">
              Cancel
            </button>
            <button class="btn btn-warning" @click="confirmRelease">
              Release
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showReleaseModal" class="modal-backdrop fade show"></div>
  </div>
</template>

<script>
import axios from 'axios'
import UserNavbar from '../components/UserNavbar.vue'

export default {
  name: 'UserReservations',
  components: { UserNavbar },

  data() {
    return {
      user: null,
      loading: true,
      error: '',
      showReleaseModal: false,
      activeReservation: null
    }
  },
  computed: {
    now() {
      return new Date().toISOString()
    },
    estimatedCost() {
      if (!this.activeReservation) return 0
      const start = new Date(this.activeReservation.start_time)
      const end = new Date()
      const hours = Math.ceil((end - start) / (1000 * 60 * 60)) || 1
      return hours * 20 // ₹20/hour
    }
  },
  methods: {
    async fetchReservations() {
      this.loading = true
      try {
        const res = await axios.get('http://localhost:5000/user/dashboard', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        })
        this.user = res.data
      } catch (err) {
        console.error(err)
        if (err.response?.status === 401) {
          this.error = 'Session expired. Please log in again.'
          localStorage.clear()
          this.$router.push('/login')
        } else {
          this.error = 'Failed to load reservations.'
        }
      } finally {
        this.loading = false
      }
    },
    formatDate(dateStr) {
      return new Date(dateStr).toLocaleString()
    },
    releaseSpot(reservationId) {
      const reservation = this.user.reservations.find(r => r.reservation_id === reservationId)
      if (reservation) {
        this.activeReservation = { ...reservation }
        this.showReleaseModal = true
      }
    },
    async confirmRelease() {
      try {
        await axios.post(
          'http://localhost:5000/user/release',
          { reservation_id: this.activeReservation.reservation_id },
          { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
        )
        this.showReleaseModal = false
        this.fetchReservations()
      } catch (err) {
        console.error(err)
        alert(err.response?.data?.msg || 'Failed to release spot.')
      }
    }
  },
  mounted() {
    this.fetchReservations()
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
  padding: 1.5rem 2rem;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--primary);
  text-align: center;
  margin-bottom: 1.5rem;
}

/* Loader */
.loader-container {
  text-align: center;
  margin-top: 2rem;
}
.loader-text {
  margin-top: 0.75rem;
  font-size: 0.95rem;
  color: var(--secondary);
}

/* Grid of cards */
.cards-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  margin-bottom: 2rem;
}

/* Individual reservation card */
.reservation-card {
  background: #fff;
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.reservation-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8f9fa;
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
}
.header-text h5 {
  margin: 0;
  font-size: 1.125rem;
}
.header-text small {
  color: #6c757d;
}

.card-body {
  padding: 1rem;
}
.info {
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.btn-warning {
  background-color: #ffc107;
  border: none;
}
.btn-warning:hover {
  background-color: #e0a800;
}

.no-reservations {
  text-align: center;
  color: #6c757d;
  font-size: 1rem;
  margin-top: 3rem;
}
</style>
