export function HelpView() {
  return (
    <div className="help">
      <h1>Setting up Atlas</h1>
      <p>
        Atlas runs entirely on your Mac and talks to your own ServiceNow instance. Nothing is
        hosted anywhere. Follow these steps once to connect it.
      </p>

      <h3>1. Install the Atlas app on your ServiceNow instance</h3>
      <p>
        Atlas reads and writes a set of custom tables that live in a ServiceNow scoped app.
        That app has to be installed on <em>your</em> instance first — Atlas can't create it
        remotely. You'll need admin on the instance.
      </p>
      <ul>
        <li>Deploy the Fluent app in <code>servicenow/</code> with the ServiceNow SDK
            (<code>now-sdk install</code>), or import it as an update set.</li>
        <li>This is a one-time step per instance. Ask whoever shared Atlas with you for the
            app package if you don't have the <code>servicenow/</code> source.</li>
      </ul>

      <h3>2. Create (or pick) a ServiceNow user for Atlas</h3>
      <p>
        Atlas signs in with basic auth. Use a user that is <strong>not</strong> MFA-enrolled
        and has access to the Atlas tables. A dedicated integration-style user is cleanest.
      </p>

      <h3>3. Connect in Settings</h3>
      <p>
        Open <strong>Settings</strong> and enter your instance URL, username, and password,
        then <strong>Test connection</strong>. Your password is stored in the macOS Keychain —
        never in a file. Turn off <em>"Try with demo data"</em> once you're connected.
      </p>

      <h3>Just exploring?</h3>
      <p>
        Leave <em>"Try with demo data"</em> on in Settings — Atlas works fully against built-in
        sample data with no instance required.
      </p>

      <h3>Updating Atlas</h3>
      <p>
        Re-run <code>bash scripts/install.sh</code> from the source folder; it rebuilds and
        replaces the app in <code>~/Applications</code>.
      </p>
    </div>
  );
}
