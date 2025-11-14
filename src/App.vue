<template>
  <div>
    <h1>Outlook Email Viewer</h1>
    <button @click="login">Login with Outlook</button>
    <MailViewer />
  </div>
</template>

<script>
import MailViewer from './components/MailViewer.vue'
import axios from 'axios'
const restapi = import.meta.env.VITE_REST_API_ROOT;


export default {
  data() {
    return {
      restapiurl:restapi,
    }
  },
  components: { MailViewer },
  methods: {
    async login() {
      const res = await axios.get(this.restapiurl+"/auth/login")
      window.location.href = res.data.auth_url
    }
  }
}
</script>




<!-- <template>
  <JobRecommendations />
  <HelloWorld/>
</template>

<script setup>
import JobRecommendations from './components/JobRecommendations.vue'
import HelloWorld from './components/HelloWorld.vue'

</script> -->