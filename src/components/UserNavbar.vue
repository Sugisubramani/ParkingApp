<template>
  <nav class="navbar bg-white shadow-sm px-4 py-2 position-relative">
    <!-- Brand (Left) -->
    <div class="d-flex align-items-center">
      <router-link
        :to="dashboardRoute"
        class="navbar-brand d-flex align-items-center mb-0 text-dark text-decoration-none"
      >
        <img src="/images/parkwisee.png" alt="Parkwise Logo" class="logo-img" />
      </router-link>
    </div>

    <!-- Nav Links (Perfectly Centered) -->
    <div class="position-absolute top-50 start-50 translate-middle d-flex gap-4">
      <router-link to="/user/dashboard" class="nav-link text-dark fw-semibold">
        Home
      </router-link>
      <router-link to="/user/reservations" class="nav-link text-dark fw-semibold">
        Reservations
      </router-link>
      <router-link to="/user/summary" class="nav-link text-dark fw-semibold">
        Summary
      </router-link>
    </div>

    <!-- User Dropdown (Right-aligned) -->
    <div class="ms-auto d-flex align-items-center" v-if="username">
      <div class="dropdown">
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
            <router-link to="/user/profile" class="dropdown-item">
              Profile
            </router-link>
          </li>
          <li><hr class="dropdown-divider" /></li>
          <li>
            <a class="dropdown-item" href="#" @click.prevent="logout">
              Logout
            </a>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'UserNavbar',
  props: ['username'],
  computed: {
    dashboardRoute() {
      const role = localStorage.getItem('role');
      return role === 'admin' ? '/admin-dashboard' : '/user/dashboard';
    }
  },
  methods: {
    logout() {
      localStorage.clear();
      this.$router.push('/login');
    }
  }
}
</script>

<style scoped>
.logo-img {
  height: 32px;
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
  min-height: 56px;
}

.dropdown-menu {
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .navbar {
    flex-wrap: wrap;
  }

  .nav-links {
    position: static !important;
    transform: none !important;
    margin-top: 0.5rem;
    justify-content: center;
    width: 100%;
  }
}
</style>
