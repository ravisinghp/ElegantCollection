<template>
  <div>
    <h2>Mails</h2>
    <div v-if="emails.length === 0">No emails yet</div>
    <ul>
      <li v-for="email in emails" :key="email.id">
        <strong>{{ email.subject }}</strong> - {{ email.from }}
        <p>{{ email.bodyPreview }}</p>
        <ul>
          <li v-for="att in email.attachments" :key="att">📎 {{ att }}</li>
        </ul>
      </li>
    </ul>
  </div>
</template>

<script>
import axios from 'axios'
const restapi = import.meta.env.VITE_REST_API_ROOT;


export default {
  name: "MailViewer",
  data() {
    return {
      emails: [],
      token: null,
      restapiurl:restapi,

    }
  },
   async mounted() {
    const params = new URLSearchParams(window.location.search)
    const token = params.get("token")
    if (token) {
      this.token = token
      try {
        const emailRes = await axios.post(this.restapiurl+"/auth/emails", {
          access_token: this.token
        })
        console.log("Fetched emails:", emailRes.data)
        this.emails = emailRes.data
      } catch (err) {
        console.error("Failed to fetch emails", err)
      }
    } else {
      console.warn("No access token found in URL")
    }
  }
  
  // async mounted() {
  //   const params = new URLSearchParams(window.location.search)
  //   const code = params.get("code")
  //   if (code) {
  //     try {
  //       const res = await axios.get(this.restapiurl+`/auth/callback?code=${code}`)
  //       this.token = res.data.access_token

  //       const emailRes = await axios.post(this.restapiurl+"/auth/emails", {
  //         access_token: this.token
  //       })
  //       this.emails = emailRes.data
  //     } catch (err) {
  //     console.error("Error during token exchange or mail fetch:", err)
  //   }
  //   }
  // }
}
</script>
