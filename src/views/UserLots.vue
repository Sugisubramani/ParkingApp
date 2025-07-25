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
    <div class="booking-modal" v-if="showModal" @click.self="closeModal">
      <div class="modal-dialog">
        <div class="modal-content shadow rounded-4">
          <div class="modal-header bg-dark text-white px-4 py-3">
            <h5 class="modal-title fw-semibold">Confirm Parking Spot</h5>
            <button type="button" class="btn-close btn-close-white" @click="closeModal" />
          </div>
          <div class="modal-body px-4 py-3">
            <div class="mb-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="text-muted">Parking Lot</span>
                <strong>{{ bookingData.lotName }}</strong>
              </div>
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="text-muted">Spot Number</span>
                <strong>#{{ bookingData.spotNumber }}</strong>
              </div>
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="text-muted">User ID</span>
                <strong>{{ user.id }}</strong>
              </div>
              <div class="d-flex justify-content-between align-items-center mb-3">
                <span class="text-muted">Rate per Hour</span>
                <strong class="text-success">₹{{ bookingData.cost }}</strong>
              </div>
              <div class="d-flex justify-content-between align-items-center mb-3">
                <span class="text-muted">Start Time</span>
                <strong>{{ formatDateIST(bookingData.startTime) }}</strong>
              </div>
            </div>
            <hr />
            <div class="mb-3">
              <label class="form-label fw-semibold">Enter Vehicle Number</label>
              <input v-model="vehicleNumber" type="text" class="form-control form-control-lg shadow-sm"
                placeholder="e.g. TN01AB1234" />
            </div>
          </div>
          <div class="modal-footer bg-light px-4 py-3 d-flex justify-content-between">
            <button class="btn btn-outline-dark" @click="closeModal">Cancel</button>
            <button class="btn btn-success px-4" :disabled="!vehicleNumber" @click="confirmBooking">
              Confirm Booking
            </button>
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
            <select v-model="searchField" class="form-select styled-dropdown">
              <option value="name">Lot Name</option>
              <option value="location">Address</option>
              <option value="pincode">Pincode</option>
            </select>
          </div>
          <div class="col">
            <input v-model="searchQuery" type="text" class="form-control shadow-sm" placeholder="Search..." />
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
                  <p class="text-muted small mb-0">{{ lot.location }}</p>
                  <p class="text-muted small mb-3">Pincode: {{ lot.pincode || 'N/A' }}</p>
                  <ul class="list-unstyled mb-0 small">
                    <li><strong>Total:</strong> {{ lot.total_spots }}</li>
                    <li><strong>Free:</strong> {{ lot.available_spots }}</li>
                    <li><strong>Rate:</strong> ₹{{ lot.price_per_hour }}</li>
                  </ul>
                </div>
                <button class="btn btn-outline-primary mt-3 w-100" :disabled="lot.available_spots === 0"
                  @click="openBookingModal(lot)">
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
import { DateTime } from 'luxon';


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
        cost: 0,
        startTime: null    // ← initialize here
      }
    }
  },
  computed: {
    filteredLots() {
      const q = this.searchQuery.trim().toLowerCase()
      if (!q) return this.lots
      return this.lots.filter(lot => {
        const val = (lot[this.searchField] || '').toString().toLowerCase()
        return val.includes(q)
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
          axios.get('http://localhost:5000/user/dashboard', { headers: { Authorization: `Bearer ${token}` } }),
          axios.get('http://localhost:5000/user/lots',      { headers: { Authorization: `Bearer ${token}` } })
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
  const token = localStorage.getItem('token');
  try {
    const res = await axios.post(
      'http://localhost:5000/user/assign',
      { lot_id: lot.id },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    
    // Set start time to current IST time
    const nowIST = DateTime.now().setZone('Asia/Kolkata').toISO();
    
    this.bookingData = {
      lotId: lot.id,
      lotName: lot.name,
      spotNumber: res.data.spot_number,
      reservationId: res.data.reservation_id,
      cost: res.data.cost,
      startTime: nowIST // Use current IST time
    };
    this.vehicleNumber = '';
    this.showModal = true;
  } catch {
    alert('Could not hold a spot.');
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
      } catch {
        alert('Booking failed.')
      }
    },
    closeModal() {
      this.showModal = false
    },
     formatDateIST(dateStr) {
      if (!dateStr) return 'N/A';
      // Parse with explicit India timezone
      const ist = DateTime.fromISO(dateStr).setZone('Asia/Kolkata');
      return ist.isValid 
        ? ist.toFormat("dd LLL yyyy, hh:mm a 'IST'") 
        : 'Invalid Date';
    },

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

/* Make the search row stretch */
.search-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  width: 100%;
}

/* Ensure the input fills the remaining space */
.search-row .form-control {
  flex: 1 1 auto;
  width: 100%;
  border: 1px solid #000;
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
}

/* Give the dropdown a solid black border on all sides */
.styled-dropdown {
  flex: 0 0 auto;
  border: 1px solid #000 !important;
  border-radius: 0.5rem;
  padding: 0.5rem 1.5rem 0.5rem 0.75rem;
  background-color: #fff;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 140 140' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath fill='%23000' d='M0 20l70 100 70-100z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 0.65rem;
  box-sizing: border-box;
}

/* Keep the black border on focus/open */
.styled-dropdown:focus {
  outline: none;
  border-color: #000 !important;
  box-shadow: 0 0 0 1px #000;
}

.card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

.card:hover {
  transform: translateY(-4px) scale(1.015);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.card-title {
  font-weight: 600;
}

.booking-modal {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.booking-modal .modal-dialog {
  max-width: 500px;
  width: 100%;
}

.booking-modal .modal-content {
  border: none;
  background-color: #fff;
  animation: fadeIn 0.25s ease-out;
}

.booking-modal .modal-header {
  border-bottom: none;
  border-top-left-radius: 1rem;
  border-top-right-radius: 1rem;
}

.booking-modal .modal-footer {
  border-top: none;
  border-bottom-left-radius: 1rem;
  border-bottom-right-radius: 1rem;
}

.booking-modal input.form-control {
  border-radius: 0.5rem;
  font-size: 1rem;
}

.booking-modal .btn {
  border-radius: 0.5rem;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.96);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
