<template>
  <div v-if="loading" class="loader-container">
    <div class="spinner-border text-primary" role="status"></div>
    <p class="loader-text">Loading parking lots…</p>
  </div>

  <div v-else-if="error" class="alert alert-danger text-center mt-4">
    {{ error }}
  </div>

  <div v-else class="dashboard-wrapper bg-light d-flex flex-column min-vh-100">
    <UserNavbar :username="user.username || user.email" />

    <!-- Booking Modal -->
    <div class="custom-modal" v-if="showModal" @click.self="closeModal">
      <div class="modal-dialog">
        <div class="modal-content shadow-sm rounded">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title">Confirm Booking</h5>
            <button type="button" class="btn-close" @click="closeModal" />
          </div>
          <div class="modal-body">
            <p><strong>Lot:</strong> {{ bookingData.lotName }}</p>
            <p><strong>Spot #:</strong> {{ bookingData.spotNumber }}</p>
            <p><strong>User ID:</strong> {{ user.id }}</p>
            <p><strong>Rate/hr:</strong> ₹{{ bookingData.cost }}</p>
            <div class="mb-3">
              <label class="form-label">Vehicle Number</label>
              <input
                v-model="vehicleNumber"
                type="text"
                class="form-control"
                placeholder="Enter vehicle number"
              />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline-secondary" @click="closeModal">Cancel</button>
            <button class="btn btn-primary" :disabled="!vehicleNumber" @click="confirmBooking">Confirm</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <section class="main-content flex-grow-1 py-4 d-flex justify-content-center overflow-auto">
      <div class="container-lg px-3">
        <!-- Search Row -->
        <div class="row align-items-center g-3 mb-4 search-row">
          <div class="col-auto">
            <label class="form-label mb-0 fw-semibold">Search by:</label>
          </div>
          <div class="col-auto">
            <select v-model="searchField" class="form-select shadow-sm">
              <option value="location">Location</option>
              <option value="address">Address</option>
              <option value="pincode">Pincode</option>
            </select>
          </div>
          <div class="col">
            <input
              v-model="searchQuery"
              type="text"
              class="form-control shadow-sm"
              placeholder="Enter search term"
            />
          </div>
        </div>

        <!-- Heading -->
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h4 class="fw-bold">Available Parking Lots</h4>
        </div>

        <!-- Lots Grid -->
        <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
          <div v-for="lot in filteredLots" :key="lot.id" class="col">
            <div class="card h-100 border-0 shadow-sm rounded-3">
              <div class="card-body d-flex flex-column justify-content-between">
                <div>
                  <h5 class="card-title mb-2 fw-semibold">{{ lot.name }}</h5>
                  <p class="text-muted small mb-3">{{ lot.location }}</p>
                  <ul class="list-unstyled mb-0 small">
                    <li><strong>Total:</strong> {{ lot.total_spots }}</li>
                    <li><strong>Free:</strong> {{ lot.available_spots }}</li>
                    <li><strong>Rate:</strong> ₹{{ lot.price_per_hour }}</li>
                  </ul>
                </div>
                <button
                  class="btn btn-outline-primary mt-3 w-100"
                  :disabled="lot.available_spots === 0"
                  @click="openBookingModal(lot)"
                >
                  Book Spot
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
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
      user: null,
      lots: [],
      loading: true,
      error: '',
      showModal: false,
      vehicleNumber: '',
      searchField: 'location',
      searchQuery: '',
      bookingData: {
        lotId: null,
        lotName: '',
        spotNumber: null,
        reservationId: null,
        cost: 0
      }
    }
  },
  computed: {
    filteredLots() {
      const query = this.searchQuery.trim().toLowerCase()
      if (!query) return this.lots

      return this.lots.filter(lot => {
        if (this.searchField === 'location' || this.searchField === 'address') {
          return lot.location.toLowerCase().includes(query)
        } else if (this.searchField === 'pincode') {
          const pincode = lot.location.match(/\b\d{6}\b/)?.[0] || ''
          return pincode.includes(query)
        }
        return false
      })
    }
  },
  methods: {
    async fetchData() {
      this.loading = true
      this.error = ''
      const token = localStorage.getItem('token')
      try {
        const [userRes, lotsRes] = await Promise.all([
          axios.get('http://localhost:5000/user/dashboard', {
            headers: { Authorization: `Bearer ${token}` }
          }),
          axios.get('http://localhost:5000/user/lots', {
            headers: { Authorization: `Bearer ${token}` }
          })
        ])
        this.user = userRes.data
        this.lots = lotsRes.data
      } catch (err) {
        if (err.response?.status === 401) {
          this.error = 'Session expired. Please log in again.'
          localStorage.clear()
          this.$router.push('/login')
        } else {
          this.error = 'Failed to load data.'
        }
      } finally {
        this.loading = false
      }
    },
    async openBookingModal(lot) {
      const token = localStorage.getItem('token')
      try {
        const res = await axios.post(
          'http://localhost:5000/user/assign',
          { lot_id: lot.id },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        this.bookingData = {
          lotId: lot.id,
          lotName: lot.name,
          spotNumber: res.data.spot_number,
          reservationId: res.data.reservation_id,
          cost: res.data.cost
        }
        this.vehicleNumber = ''
        this.showModal = true
      } catch (err) {
        alert(err.response?.data?.msg || 'Could not hold a spot.')
      }
    },
    async confirmBooking() {
      const token = localStorage.getItem('token')
      try {
        await axios.post(
          'http://localhost:5000/user/reserve',
          {
            reservation_id: this.bookingData.reservationId,
            vehicle_number: this.vehicleNumber
          },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        this.showModal = false
        this.$router.push('/user/reservations')
      } catch (err) {
        alert(err.response?.data?.msg || 'Booking failed.')
      }
    },
    closeModal() {
      this.showModal = false
    }
  },
  mounted() {
    this.fetchData()
  }
}
</script>

<style scoped>
.loader-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem 0;
}

.loader-text {
  margin-top: 1rem;
  font-size: 1rem;
  color: #555;
}

.dashboard-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  background-color: #f9f9f9;
}

.search-row .form-select,
.search-row .form-control {
  max-width: 100%;
}

.card {
  transition: box-shadow 0.2s ease;
}

.card:hover {
  box-shadow: 0 0 12px rgba(0, 0, 0, 0.08);
}

.card-title {
  font-weight: 600;
}

/* Modal */
.custom-modal {
  position: fixed;
  inset: 0;
  z-index: 1055;
  background-color: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  overflow-y: auto;
}

.modal-dialog {
  max-width: 500px;
  width: 100%;
}
</style>
