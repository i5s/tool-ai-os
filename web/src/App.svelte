<script>
  import './styles.js'
  import Shell from './layouts/Shell.svelte'
  import { theme } from './lib/theme.js'

  let initial = $state(localStorage.getItem('theme'))
  document.documentElement.classList.toggle('light', initial === 'light')

  theme.subscribe(val => {
    document.documentElement.classList.toggle('light', val === 'light')
  })
</script>

<Shell />
