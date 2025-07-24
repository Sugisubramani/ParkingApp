<template>
  <div class="dashboard-wrapper">
    <UserNavbar :username="user?.username || 'User'" />

    <div class="scroll-area">
      <div v-if="loading" class="loader-container">
        <div class="spinner-border text-primary" role="status"></div>
        <p class="loader-text">Loading reservations…</p>
      </div>

      <div v-else-if="error" class="alert alert-danger text-center mt-4">{{ error }}</div>

      <section v-else>
        <h2 class="section-title mb-4">Your Reservations</h2>
        <ul v-if="user.reservations?.length" class="list-group reservation-list">
          <li
            v-for="r in user.reservations"
            :key="r.reservation_id"
            class="list-group-item reservation-item d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center"
          >
            <div class="reservation-info">
              <span><strong>Lot:</strong> {{ r.lot_name }}</span>
              <span><strong>Address:</strong> {{ r.lot_address }}</span>
              <span><strong>Spot:</strong> #{{ r.spot_number }}</span>
              <span><strong>Vehicle:</strong> {{ r.vehicle_number }}</span>
              <span><strong>Start:</strong> {{ formatDate(r.start_time) }}</span>
              <span><strong>End:</strong> {{ r.end_time ? formatDate(r.end_time) : 'Ongoing' }}</span>
            </div>
            <button class="btn btn-outline-warning btn-sm mt-3 mt-md-0" @click="releaseSpot(r.reservation_id)">
              Release
            </button>
          </li>
        </ul>
        <p v-else class="text-muted text-center fs-6">No reservations found.</p>
      </section>
    </div>
  </div>

  <!-- Release Modal -->
  <div class="modal fade" tabindex="-1" :class="{ show: showReleaseModal }" style="display: block;" v-if="showReleaseModal">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Release Reservation</h5>
          <button type="button" class="btn-close" @click="showReleaseModal = false"></button>
        </div>
        <div class="modal-body">
          <ul class="list-group list-group-flush">
            <li class="list-group-item"><strong>Lot:</strong> {{ activeReservation.lot_name }}</li>
            <li class="list-group-item"><strong>Spot:</strong> #{{ activeReservation.spot_number }}</li>
            <li class="list-group-item"><strong>Vehicle:</strong> {{ activeReservation.vehicle_number }}</li>
            <li class="list-group-item"><strong>Start Time:</strong> {{ formatDate(activeReservation.start_time) }}</li>
            <li class="list-group-item"><strong>Release Time:</strong> {{ formatDate(now) }}</li>
            <li class="list-group-item"><strong>Estimated Cost:</strong> ₹{{ estimatedCost }}</li>
          </ul>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showReleaseModal = false">Cancel</button>
          <button class="btn btn-warning" @click="confirmRelease">Release</button>
        </div>
      </div>
    </div>
  </div>
  <div v-if="showReleaseModal" class="modal-backdrop fade show"></div>
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
      const token = localStorage.getItem('token')
      try {
        const res = await axios.get('http://localhost:5000/user/dashboard', {
          headers: { Authorization: `Bearer ${token}` }
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
    async releaseSpot(reservationId) {
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
        this.activeReservation = null
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
  padding: 2rem 1rem;
}

.section-title {
  font-size: 1.625rem;
  font-weight: 600;
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
  font-size: 0.95rem;
}

/* Reservations */
.reservation-list {
  padding: 0;
  margin-bottom: 2rem;
}

.reservation-item {
  background: var(--card-bg);
  border: none;
  border-radius: 0.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, .05);
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
  transition: box-shadow 0.2s ease;
}

.reservation-item:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, .08);
}

.reservation-info span {
  display: block;
  font-size: 0.95rem;
  margin-bottom: 0.3rem;
}

@media (min-width: 768px) {
  .reservation-info span {
    display: inline-block;
    margin-right: 1.5rem;
    margin-bottom: 0;
  }
}
</style>
