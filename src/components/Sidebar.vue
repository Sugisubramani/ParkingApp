<template>
  <div class="sidebar d-flex flex-column text-white p-3">
    <!-- Top Profile Section with Dropdown -->
    <div class="mb-4 position-relative">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <h5 class="mb-0">Admin</h5>
          <small class="text-light">Welcome, {{ username }}!</small>
        </div>
        <div class="dropdown">
          <button class="btn btn-sm btn-secondary dropdown-toggle" type="button" id="profileDropdown"
            data-bs-toggle="dropdown" aria-expanded="false">
            <i class="bi bi-chevron-down"></i>
          </button>
          <ul class="dropdown-menu dropdown-menu-dark" aria-labelledby="profileDropdown">
            <li>
              <button class="dropdown-item" type="button" @click="$emit('change-view', 'profile')">
                <i class="bi bi-person me-2"></i>View Profile
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Sidebar Navigation -->
    <div class="mt-3 flex-grow-1">
      <!-- 1) HOME at the top -->
      <button class="btn btn-outline-light w-100 mb-2" @click="$emit('change-view', 'home')">
        <i class="bi bi-house-door me-2"></i>Home
      </button>

      <button class="btn btn-outline-light w-100 mb-2" @click="$emit('change-view', 'users')">
        <i class="bi bi-people me-2"></i>Users
      </button>

  <button class="btn btn-outline-light w-100 mb-2" @click="$emit('change-view', 'dashboard')">
    <i class="bi bi-speedometer2 me-2"></i>Dashboard
  </button>
    
    </div>

    <!-- Logout -->
    <div>
      <button class="btn btn-danger w-100" @click="$emit('logout')">
        <i class="bi bi-box-arrow-right me-2"></i>Logout
      </button>
    </div>
  </div>
</template>

<script>
export default {
  props: ['username']
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  background-color: #343a40;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

/* Hide Bootstrap's default caret so only your <i> remains */
.dropdown-toggle::after {
  display: none;
}
</style>
