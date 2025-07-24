<template>
  <nav class="navbar bg-white shadow-sm px-4 py-2">
    <!-- Brand -->
    <router-link
      :to="dashboardRoute"
      class="navbar-brand d-flex align-items-center mb-0 text-dark text-decoration-none"
    >
      <img src="/images/parkwisee.png" alt="Parkwise Logo" class="logo-img" />
    </router-link>

    <!-- Navigation Links -->
    <div class="nav-links d-flex gap-4 ms-4">
      <router-link to="/user/dashboard" class="nav-link text-dark fw-semibold">
        Dashboard
      </router-link>
      <router-link to="/user/reservations" class="nav-link text-dark fw-semibold">
        Reservations
      </router-link>
    </div>

    <!-- User Dropdown -->
    <div class="dropdown ms-auto" v-if="username">
      <button
        class="btn btn-light dropdown-toggle d-flex align-items-center"
        type="button"
        id="userMenu"
        data-bs-toggle="dropdown"
        aria-expanded="false"
      >
        <i class="bi bi-person-circle me-2 fs-5"></i>
        <span class="fw-semibold">{{ username }}</span>
      </button>
      <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="userMenu">
        <li>
          <a class="dropdown-item" href="#" @click.prevent="logout">Logout</a>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'UserNavbar',
  props: ['username'],
  computed: {
    dashboardRoute() {
      const role = localStorage.getItem('role')
      return role === 'admin' ? '/admin-dashboard' : '/user/dashboard'
    }
  },
  methods: {
    logout() {
      localStorage.clear()
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.logo-img {
  height: 32px;
  width: auto;
  object-fit: contain;
  display: block;
}

.navbar-brand:hover,
.nav-link:hover {
  color: #0d6efd !important;
  text-decoration: none;
}

.nav-link {
  font-size: 0.95rem;
  text-decoration: none;
}

.navbar {
  display: flex;
  align-items: center;
}
</style>
