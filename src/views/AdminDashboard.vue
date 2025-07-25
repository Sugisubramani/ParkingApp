<template>
  <div class="d-flex vh-100">
    <!-- Sidebar -->
    <Sidebar :username="username" @change-view="changeView" @logout="logout" />

    <!-- Main Content Pane -->
    <div class="main-content flex-grow-1 bg-light overflow-auto">

      <!-- Profile / Edit in one pane -->
      <div v-if="currentView === 'profile'" class="d-flex justify-content-center align-items-center"
        style="height:100%">
        <div class="card profile-card p-4 shadow-sm">
          <h4 class="mb-4 text-center">Admin Profile</h4>
          <form @submit.prevent="saveProfile">
            <div class="mb-3">
              <label class="form-label">Email</label>
              <input v-model="profileForm.email" type="email" class="form-control" disabled />
            </div>
            <div class="mb-3 position-relative">
              <label class="form-label">Password</label>
              <input :type="showPassword ? 'text' : 'password'" v-model="profileForm.password" class="form-control"
                placeholder="Password" />
              <i :class="showPassword ? 'bi bi-eye-slash-fill' : 'bi bi-eye-fill'" class="password-eye"
                @click="showPassword = !showPassword"></i>
            </div>
            <div class="d-flex justify-content-between">
              <button type="button" class="btn btn-outline-secondary" @click="changeView('dashboard')">
                <i class="bi bi-arrow-left me-1"></i>Back
              </button>
              <button type="submit" class="btn btn-primary">Save Changes</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Dashboard View -->
      <div v-else-if="currentView === 'dashboard'" class="p-4">
        <div class="row text-center g-3 mb-4">
          <div class="col" v-for="(label, key) in {
            'Total Lots': 'totalLots',
            'Total Spots': 'totalSpots',
            Available: 'availableSpots',
            Reserved: 'reservedSpots'
          }" :key="key">
            <div class="stat-box bg-white rounded shadow-sm p-3">
              <h6 class="stat-title">{{ key }}</h6>
              <h4 class="stat-value" :class="{
                'text-primary': key === 'Total Lots',
                'text-success': key === 'Total Spots',
                'text-info': key === 'Available',
                'text-danger': key === 'Reserved'
              }">
                {{ stats[label] }}
              </h4>
            </div>
          </div>
        </div>

        <div class="row g-4">
          <!-- Availability Summary (Bar) -->
          <div class="col-lg-6">
            <h5 class="mt-4">Availability Summary</h5>
            <div class="chart-container" style="height:400px;position:relative;">
              <canvas ref="availabilityChart" style="width:100%; height:100%;"></canvas>
            </div>
          </div>

          <!-- Revenue by Lot (Pie) -->
          <div class="col-lg-6">
            <h5 class="mt-4">Revenue by Lot</h5>
            <div class="chart-container" style="height:400px;position:relative;">
              <canvas ref="revenuePieChart" style="width:100%; height:100%;"></canvas>
            </div>
          </div>
        </div>
      </div>
      <!-- Home View -->
      <div v-if="currentView === 'home'" class="p-4">

        <!-- 1) Add Lot Button -->
<div class="d-flex justify-content-center mb-4">
  <button class="btn btn-primary" @click="showNewLotModal = true">
    + Add Lot
  </button>
</div>

        <!-- Search Bar -->
        <div class="d-flex align-items-center mb-3">
          <!-- Dropdown for search-by field -->
          <select v-model="searchBy" class="form-select w-auto me-2">
            <option value="userId">User ID</option>
            <option value="location">Location</option>
            <option value="pincode">Pincode</option>
          </select>

          <!-- Text input for search query -->
          <input v-model="searchQuery" type="text" placeholder="Enter search term" class="form-control me-2" />

          <!-- Search button -->
          <button class="btn btn-primary me-2" @click="performSearch()">
            Search
          </button>

          <!-- Clear search -->
          <button class="btn btn-outline-secondary" @click="clearSearch()">
            Clear
          </button>
        </div>


        <!-- 2) New Parking Modal -->
        <div v-if="showNewLotModal" class="modal-backdrop" @click.self="showNewLotModal = false">
          <div class="modal-content p-4 shadow">
            <h5>New Parking</h5>

            <div class="mb-2">
              <label class="form-label">Prime Location Name</label>
              <input v-model="newLot.name" class="form-control" />
            </div>
            <div class="mb-2">
              <label class="form-label">Address</label>
              <input v-model="newLot.address" class="form-control" />
            </div>
            <div class="mb-2">
              <label class="form-label">Pincode</label>
              <input v-model="newLot.pincode" class="form-control" />
            </div>
            <div class="mb-2">
              <label class="form-label">Price (per hour)</label>
              <input v-model="newLot.price" type="number" class="form-control" />
            </div>
            <div class="mb-3">
              <label class="form-label">Maximum Spots</label>
              <input v-model="newLot.maxSpots" type="number" class="form-control" />
            </div>

            <div class="text-end">
              <button class="btn btn-secondary me-2" @click="showNewLotModal = false">
                Cancel
              </button>
              <button class="btn btn-primary" @click="addNewLot">
                Add
              </button>
            </div>
          </div>
        </div>
        <!-- 3) Parking Lots List -->
        <div v-if="parkingLots.length">
          <div v-for="lot in parkingLots" :key="lot.id"
            class="lot-card bg-white shadow-sm p-3 mb-2 d-flex justify-content-between align-items-center">
            <div>
              <strong>{{ lot.name }}</strong>
              (Occupied = {{lot.spots.filter(s => !s.is_available).length}}
              /{{ lot.spots.length }})
            </div>

            <div class="btn-group btn-group-sm">
              <!-- Edit icon -->
              <button class="btn btn-outline-secondary" @click="openEditLot(lot)">
                <i class="bi bi-pencil-square"></i>
              </button>

              <!-- View icon -->
              <button class="btn btn-outline-primary" @click="viewLot(lot)">
                View
              </button>

              <!-- Delete icon: only if no occupied spots -->
              <button v-if="lot.spots.filter(s => !s.is_available).length === 0" class="btn btn-outline-danger"
                @click="deleteLot(lot.id)">
                <i class="bi bi-trash"></i>
              </button>
            </div>

          </div>
        </div>

        <div v-else class="text-muted">No parking lots yet.</div>

        <!-- 4) Lot Details Modal -->
        <div v-if="showLotDetails" class="modal-backdrop" @click.self="showLotDetails = false">
          <div class="modal-content p-4 shadow">
            <h5>{{ selectedLot.name }}</h5>
            <p>Address: {{ selectedLot.location }}</p>
            <p>Pincode: {{ selectedLot.pincode }}</p>
            <p>Price/hr: {{ selectedLot.price_per_hour }}</p>
            <p>Spots: {{ selectedLot.spots.length }}</p>

            <div class="d-flex flex-wrap mt-3">
              <div v-for="spot in selectedLot.spots" :key="spot.id"
                class="spot-box m-1 d-flex justify-content-center align-items-center" :class="{
                  'bg-success': spot.is_available,
                  'bg-danger': !spot.is_available
                }" @click="onSpotClick(spot)">
                {{ spot.number }}

              </div>
            </div>


            <div class="text-end mt-3">
              <button class="btn btn-secondary" @click="showLotDetails = false">
                Close
              </button>
            </div>
          </div>
        </div>
      </div>


      <!-- Edit Lot Modal -->
      <div v-if="showEditLotModal" class="modal-backdrop" @click.self="showEditLotModal = false">
        <div class="modal-content p-4 shadow">
          <h5>Edit Parking Lot</h5>

          <div class="mb-2">
            <label class="form-label">Name</label>
            <input v-model="editLotForm.name" class="form-control" />
          </div>

          <div class="mb-2">
            <label class="form-label">Location</label>
            <input v-model="editLotForm.location" class="form-control" />
          </div>

          <div class="mb-2">
            <label class="form-label">Pincode</label>
            <input v-model="editLotForm.pincode" class="form-control" />
          </div>

          <div class="mb-2">
            <label class="form-label">Price/hr</label>
            <input v-model="editLotForm.price_per_hour" type="number" class="form-control" />
          </div>


          <div class="text-end">
            <button class="btn btn-secondary me-2" @click="showEditLotModal = false">
              Cancel
            </button>
            <button class="btn btn-primary" @click="saveEditedLot()">
              Save
            </button>
          </div>
        </div>
      </div>


      <!-- Users View -->
      <div v-else-if="currentView === 'users'" class="p-4">
        <h4>Registered Users</h4>

        <table class="table table-bordered mt-3">
          <thead class="table-light">
            <tr>
              <th>ID</th>
              <th>Email</th>
              <th>Fullname</th>
              <th>Address</th>
              <th>Pincode</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="(u, idx) in users" :key="u.id">
              <!-- use idx+1 for your ID column -->
              <td>{{ idx + 1 }}</td>
              <td>{{ u.email }}</td>
              <td>{{ u.fullname }}</td>
              <td>{{ u.address }}</td>
              <td>{{ u.pincode }}</td>
            </tr>
            <tr v-if="!users.length">
              <td colspan="5" class="text-center text-muted">No users found</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Spot Details Modal -->
      <div v-if="showSpotModal" class="modal-backdrop" @click.self="showSpotModal = false">
        <div class="modal-content p-4 shadow">
          <h5>
            Spot #{{ selectedSpot.number }} –
            <span v-if="selectedSpot.is_available">Available</span>
            <span v-else>Occupied</span>
          </h5>

          <!-- Available Spot -->
          <template v-if="selectedSpot.is_available">
            <p>Status: Available</p>
            <div class="text-end">
              <button class="btn btn-danger me-2" @click="deleteSpot(selectedLot.id, selectedSpot.id)">
                Delete Spot
              </button>

              <button class="btn btn-secondary" @click="showSpotModal = false">
                Close
              </button>
            </div>
          </template>

          <!-- Occupied Spot -->
          <template v-else>
            <ul class="list-unstyled mb-3">
              <li><strong>ID:</strong> {{ spotDetails.customer_id }}</li>
              <li><strong>Vehicle No:</strong> {{ spotDetails.vehicle_no }}</li>
              <li><strong>Start Time:</strong> {{ spotDetails.start_time }}</li>
              <li><strong>Est Cost:</strong> {{ spotDetails.est_cost }}</li>
            </ul>
            <div class="text-end">
              <button class="btn btn-secondary" @click="showSpotModal = false">
                Close
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);


import axios from 'axios'


export default {
  components: { Sidebar },
  data() {
    return {
      username: '',
      parkingLots: [],
      allParkingLots: [],
      users: [],
      currentView: 'dashboard',
      form: { name: '', location: '', spot: '' },
      newSpots: {},
      stats: {
        totalLots: 0,
        totalSpots: 0,
        availableSpots: 0,
        reservedSpots: 0,
        lotSummary: []
      },

      showPassword: false,
      profileForm: {
        email: 'admin@example.com',
        password: localStorage.getItem('password') || ''
      },

      // ← NEW STATE for Home view
      showNewLotModal: false,
      newLot: {
        name: '',
        address: '',
        pincode: '',
        price: null,
        maxSpots: null
      },
      showLotDetails: false,
      selectedLot: null,
      // 1) Which field to search by
      searchBy: 'location',

      // 2) The text you’re searching for
      searchQuery: '',
      // 1) Toggle for showing the spot modal
      showSpotModal: false,

      // 2) The spot object you clicked
      selectedSpot: null,

      // 3) Details for occupied spots (we’ll fill this next)
      spotDetails: null,

      // 1) Toggle for showing the Edit modal (moved out of stats)
      showEditLotModal: false,

      // 2) Form model for editing a lot (moved out of stats)
      editLotForm: {
        id: null,
        name: '',
        location: '',
        pincode: '',
        price_per_hour: null,
        maxSpots: null
      }
    }
  },

  watch: {
    currentView(newView) {
      if (newView === 'dashboard') {
        // Wait until the Dashboard block has been rendered
        this.$nextTick(() => {
          // Verify your refs are found
          console.log('avail ref →', this.$refs.availabilityChart)
          console.log('pie   ref →', this.$refs.revenuePieChart)
          this.renderCharts()
        })
      }
    }
  },

  methods: {
    changeView(view) {
      this.currentView = view
      if (view === 'users') this.fetchUsers()
      if (view === 'dashboard') this.fetchLots()
    },
    async saveProfile() {
      try {
        await axios.put(
          'http://127.0.0.1:5000/admin/profile',
          { password: this.profileForm.password },
          { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
        )
        // sync the new password locally so Profile View shows it
        localStorage.setItem('password', this.profileForm.password)
        alert('Password updated!')
      } catch (err) {
        alert('Update failed: ' + (err.response?.data?.msg || err.message))
      }
    },
    // ← Here’s where your search methods must live:
    performSearch() {
      const q = this.searchQuery.trim().toLowerCase();
      if (!q) {
        this.parkingLots = this.allParkingLots;
        return;
      }
      this.parkingLots = this.allParkingLots.filter(lot => {
        if (this.searchBy === 'location') {
          return lot.location.toLowerCase().includes(q);
        }
        if (this.searchBy === 'pincode') {
          return lot.pincode.toLowerCase().includes(q);
        }
        if (this.searchBy === 'userId') {
          return lot.spots.some(
            s => !s.is_available && String(s.reserved_by).toLowerCase() === q
          );
        }
        return false;
      });
    },

    async deleteSpot(lotId, spotId) {
  try {
    // 1. Optimistically remove from UI
    const lot = this.parkingLots.find(l => l.id === lotId);
    if (lot) {
      lot.spots = lot.spots.filter(s => s.id !== spotId);
    }

    // 2. Close modal IMMEDIATELY (before API call)
    this.showSpotModal = false;  // This is the key line you're missing

    // 3. Make API call in background
    const token = localStorage.getItem('token');
    await axios.delete(
      `http://localhost:5000/admin/lots/${lotId}/spots/${spotId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );

  } catch (err) {
    // If error occurs, refresh data
    this.fetchLots();
    console.error('Delete failed:', err);
  }
},
    clearSearch() {
      this.searchQuery = '';
      this.parkingLots = this.allParkingLots;
    },

    async addNewLot() {
      try {
        const token = localStorage.getItem('token')
        // POST to your new-lot endpoint
        const res = await axios.post(
          'http://127.0.0.1:5000/admin/lots',
          {
            name: this.newLot.name,
            address: this.newLot.address,
            pincode: this.newLot.pincode,
            price: this.newLot.price,
            maxSpots: this.newLot.maxSpots
          },
          { headers: { Authorization: `Bearer ${token}` } }
        )

        // on success: close modal, reset form, re-fetch server data
        this.showNewLotModal = false
        this.newLot = { name: '', address: '', pincode: '', price: null, maxSpots: null }
        await this.fetchLots()

        alert('Lot created successfully!')
      } catch (err) {
        alert('Failed to create lot: ' + (err.response?.data?.msg || err.message))
      }
    },




    // ← NEW: Show a lot’s detail modal
    viewLot(lot) {
      this.selectedLot = lot
      this.showLotDetails = true
    },

    async fetchUsers() {
      // 1) Clear out any old rows
      this.users = []

      try {
        const token = localStorage.getItem('token')
        const res = await fetch('http://127.0.0.1:5000/admin/users', {
          headers: { Authorization: `Bearer ${token}` }
        })
        const payload = await res.json()
        if (!res.ok) throw new Error(payload.msg || 'Failed to fetch users')

        // 2) Deduplicate by id
        const uniqueById = [
          ...new Map(payload.users.map(u => [u.id, u])).values()
        ]

        // 3) Assign the clean list
        this.users = uniqueById

      } catch (err) {
        alert('Could not load users: ' + err.message)
      }
    },




    async fetchLots() {
      try {
        const token = localStorage.getItem('token')
        const res = await fetch('http://127.0.0.1:5000/admin/dashboard', {
          headers: { Authorization: `Bearer ${token}` }
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.msg || 'Unauthorized')

        // Map in the new fields
        this.parkingLots = data.parking_lots.map(lot => ({
          id: lot.id,
          name: lot.name,
          location: lot.location,
          pincode: lot.pincode,
          price_per_hour: lot.price_per_hour,
          spots: lot.spots
        }))
        this.allParkingLots = this.parkingLots

        this.username = data.username || ''

        this.reservedSpots = this.parkingLots.flatMap(lot =>
          lot.spots
            .filter(s => !s.is_available)
            .map(s => ({
              lotName: lot.name,
              number: s.number,
              by: s.reserved_by,
              at: new Date(s.start_time).toLocaleString()
            }))
        )

        this.stats = {
          totalLots: data.total_lots,
          totalSpots: data.total_spots,
          availableSpots: data.available_spots,
          reservedSpots: data.reserved_spots,
          lotSummary: data.lot_summary
        };
        console.log('lotSummary from API →', this.stats.lotSummary);

        this.$nextTick(() => this.renderCharts());
      }
      catch (err) {
        alert(err.message)
        this.$router.push('/login')
      }
    },

    // Called by pencil icon
    openEditLot(lot) {
      this.editLotForm = {
        id: lot.id,
        name: lot.name,
        location: lot.location,
        pincode: lot.pincode,
        price_per_hour: lot.price_per_hour,
        maxSpots: lot.spots.length
      }
      this.showEditLotModal = true
    },

    // PUT back to server and refresh
    async saveEditedLot() {
      try {
        const token = localStorage.getItem('token')
        await axios.put(
          `http://127.0.0.1:5000/admin/lots/${this.editLotForm.id}`,
          this.editLotForm,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        this.showEditLotModal = false
        await this.fetchLots()
      } catch (err) {
        alert('Couldn’t save changes: ' + err.message)
      }
    },

    async createLot() {
      try {
        const token = localStorage.getItem('token')
        const lotRes = await fetch('http://localhost:5000/admin/lots', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({
            name: this.form.name,
            location: this.form.location
          })
        })
        const lotData = await lotRes.json()
        if (!lotRes.ok) return alert(lotData.msg)

        const spotCount = parseInt(this.form.spot)
        if (!spotCount || spotCount < 1)
          return alert('Enter valid number of spots')

        const spotRes = await fetch(
          `http://localhost:5000/admin/lots/${lotData.lot_id}/spots`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({ number: spotCount })
          }
        )
        const spotData = await spotRes.json()
        if (!spotRes.ok) return alert(spotData.msg)

        alert('Lot created!')
        this.form = { name: '', location: '', spot: '' }
        this.currentView = 'lots'
        this.fetchLots()
      } catch {
        alert('Error creating lot')
      }
    },



    async addSpot(lotId) {
      const token = localStorage.getItem('token')
      const number = parseInt(this.newSpots[lotId])
      if (!number || number < 1) return alert('Enter valid spots')
      try {
        const res = await fetch(
          `http://localhost:5000/admin/lots/${lotId}/spots`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({ number })
          }
        )
        const data = await res.json()
        if (!res.ok) return alert(data.msg)
        this.newSpots[lotId] = ''
        this.fetchLots()
      } catch {
        alert('Error adding spots')
      }
    },

    async deleteLot(lotId) {
  // 1) Confirm in the UI
  if (!confirm('Delete this empty lot for good?')) return;

  // 2) Grab token
  const token = localStorage.getItem('token');
  if (!token) {
    return alert('Not authenticated');
  }

  try {
    // 3) Call DELETE endpoint
    const res = await fetch(
      `http://127.0.0.1:5000/admin/lots/${lotId}`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        }
      }
    );

    // 4) Read back the payload
    const data = await res.json();
    console.log('DELETE /admin/lots response →', res.status, data);

    // 5) Handle errors
    if (!res.ok) {
      return alert(data.msg || `Delete failed (${res.status})`);
    }

    // 6) Success—refresh your list
    alert('Lot deleted successfully');
    this.fetchLots();
  }
  catch (err) {
    console.error('Network or parsing error:', err);
    alert('Unexpected error, check console for details');
  }
},


    promptEditSpot(lotId, spotId, currentNumber) {
      const input = prompt('Enter new spot number:', currentNumber)
      if (input === null) return
      const newNum = parseInt(input)
      if (!newNum || newNum < 1) {
        return alert('Please enter a valid number')
      }
      this.editSpot(lotId, spotId, newNum)
    },

    async editSpot(lotId, spotId, newNumber) {
      try {
        const token = localStorage.getItem('token')
        const res = await fetch(
          `http://localhost:5000/admin/lots/${lotId}/spots/${spotId}`,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({ number: newNumber })
          }
        )
        const data = await res.json()
        if (!res.ok) throw new Error(data.msg || 'Failed to update spot')
        this.fetchLots()
      } catch (err) {
        alert(err.message)
      }
    },

    confirmDeleteSpot(lotId, spotId) {
      if (!confirm('Delete this spot?')) return
      this.deleteSpot(lotId, spotId)
    },


    confirmDelete(id, name) {
      if (confirm(`Delete "${name}" and all its spots?`)) {
        this.deleteLot(id)
      }
    },

    async onSpotClick(spot) {
      // 1) Remember which spot was clicked
      this.selectedSpot = spot;

      // 2) Available spot → just show modal with no details
      if (spot.is_available) {
        this.spotDetails = null;
        this.showSpotModal = true;
        return;
      }

      // 3) Occupied spot → fetch reservation info first
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(
          `http://127.0.0.1:5000/admin/lots/${this.selectedLot.id}/spot/${spot.id}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        this.spotDetails = res.data;
        this.showSpotModal = true;
      } catch (err) {
        alert('Failed to load spot details: ' + err.message);
      }
    },

    renderCharts() {
      // 1) Availability Bar Chart
      const availCanvas = this.$refs.availabilityChart;


      if (!availCanvas) {
        console.error('availabilityChart ref not found');
        return;
      }
      const availCtx = availCanvas.getContext('2d');
      if (this._availabilityChart) this._availabilityChart.destroy();
      this._availabilityChart = new Chart(availCtx, {
        type: 'bar',
        data: {
          labels: ['Available', 'Occupied'],
          datasets: [{
            label: 'Spots',
            data: [this.stats.availableSpots, this.stats.reservedSpots],
            backgroundColor: ['#28a745', '#dc3545']
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });

      // 2) Revenue Pie Chart
      const pieCanvas = this.$refs.revenuePieChart;
      if (!pieCanvas) {
        console.error('revenuePieChart ref not found');
        return;
      }
      const pieCtx = pieCanvas.getContext('2d');
      if (this._revenuePieChart) this._revenuePieChart.destroy();

      // optional color palette
      const palette = [
        '#FF6384', '#36A2EB', '#FFCE56',
        '#4BC0C0', '#9966FF', '#FF9F40'
      ];
      const bgColors = this.stats.lotSummary.map(
        (_, i) => palette[i % palette.length]
      );

      this._revenuePieChart = new Chart(pieCtx, {
        type: 'pie',
        data: {
          labels: this.stats.lotSummary.map(l => l.name),
          datasets: [{
            data: this.stats.lotSummary.map(l => l.revenue),
            backgroundColor: bgColors
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false
        }
      });
    },

    logout() {
      localStorage.removeItem('token')
      this.$router.push('/login')
    }
  },

  mounted() {
    this.fetchLots()
  }
}
</script>


<style scoped>
.main-content {
  margin-left: 260px;
  height: 100vh;
  /* keep full height */
  overflow-y: auto;
  /* scroll if content overflows */
}

.profile-card {
  max-width: 380px;
}

/* Eye icon inside password field */
.password-eye {
  position: absolute;
  top: 70%;
  right: 0.75rem;
  transform: translateY(-50%);
  cursor: pointer;
  color: #6c757d;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background: #fff;
  border-radius: 4px;
  width: 360px;
}

.spot-box {
  width: 36px;
  height: 36px;
  color: #fff;
  font-weight: bold;
  border-radius: 4px;
}

/* Layout Tweaks */
.main-content {
  padding: 1.5rem;
  background-color: #f8f9fa;
}

/* Profile Card */
.profile-card {
  width: 100%;
  max-width: 400px;
  border-radius: 12px;
  background-color: #ffffff;
}

/* Password toggle eye icon */
.password-eye {
  position: absolute;
  top: 75%;
  right: 12px;
  transform: translateY(-50%);
  cursor: pointer;
  color: #6c757d;
}

/* Stat Box */
.stat-box {
  transition: box-shadow 0.3s ease;
  border-radius: 12px;
}
.stat-box:hover {
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.1);
}
.stat-title {
  font-size: 0.9rem;
  color: #6c757d;
}
.stat-value {
  font-size: 1.6rem;
  font-weight: bold;
}

/* Charts */
.chart-container {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 1rem;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
  padding: 1rem;
}

.modal-content {
  width: 100%;
  max-width: 500px;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 0.75rem 2rem rgba(0, 0, 0, 0.15);
  animation: fadeIn 0.25s ease-in-out;
}

/* Lot Cards */
.lot-card {
  border-radius: 8px;
  transition: transform 0.2s ease;
}
.lot-card:hover {
  transform: scale(1.01);
}

/* Spot Boxes */
.spot-box {
  width: 48px;
  height: 48px;
  font-weight: 600;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  transition: transform 0.2s ease;
}
.spot-box:hover {
  transform: scale(1.1);
}

/* Table */
.table th,
.table td {
  vertical-align: middle;
}

/* Button enhancements */
.btn {
  border-radius: 6px;
}

/* Responsive padding fix for smaller screens */
@media (max-width: 768px) {
  .main-content {
    padding: 1rem;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.97);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}


</style>
