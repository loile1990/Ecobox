package fr.lip.hownet.networkmonitor.services

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import fr.lip.hownet.networkmonitor.utils.getMACAddress
import fr.lip.hownet.networkmonitor.utils.sendUdpMessage

class ExperimentService : Service() {

    private lateinit var screenReceiver: BroadcastReceiver
    private val channelId = "ScreenServiceChannel"
    private val ipAddress = "10.20.10.1" // Hardcoded IP
    private val port = 12345 // Hardcoded port
    private val handler = Handler(Looper.getMainLooper())
    private val messageInterval: Long = 5000L
    private var currentAction: String = "On"
    private val hardcodedSsid = "ecobox"

    private val sendUdpRunnable = object : Runnable {
        override fun run() {
            Log.d(TAG, "sendUdpRunnable triggered, currentAction=$currentAction")
            sendUdpMessageForAction(currentAction)
            Log.d(TAG, "Scheduling next UDP send in $messageInterval ms")
            handler.postDelayed(this, messageInterval)
        }
    }

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "Service created")

        // Singleton check
        if (isServiceRunning) {
            Log.w(TAG, "Service already running, stopping this instance")
            stopSelf()
            return
        }
        isServiceRunning = true

        // Create notification channel
        Log.d(TAG, "Creating notification channel")
        createNotificationChannel()

        // Start foreground service immediately
        Log.d(TAG, "Starting foreground service")
        try {
            val notification = createNotification()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(1, notification,ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
            }
            else{startForeground(1, notification)}
            Log.d(TAG, "Foreground service started successfully")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start foreground service: ${e.message}")
            stopSelf()
            return
        }

        // Initialize broadcast receiver
        screenReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {
                val newAction = when (intent.action) {
                    Intent.ACTION_USER_PRESENT -> "On"
                    Intent.ACTION_SCREEN_OFF -> "Locked"
                    Intent.ACTION_SCREEN_ON -> "On"
                    else -> currentAction
                }
                if (newAction != currentAction) {
                    currentAction = newAction
                    Log.d(TAG, "Action received: $currentAction")
                    sendUdpMessageForAction(currentAction)
                }
            }
        }

        val filter = IntentFilter().apply {
            addAction(Intent.ACTION_USER_PRESENT)
            addAction(Intent.ACTION_SCREEN_OFF)
            addAction(Intent.ACTION_SCREEN_ON)
        }
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                registerReceiver(screenReceiver, filter, RECEIVER_NOT_EXPORTED)
            } else {
                registerReceiver(screenReceiver, filter)
            }
            Log.d(TAG, "Screen receiver registered")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to register receiver: ${e.message}")
        }

        handler.removeCallbacks(sendUdpRunnable)
        handler.post(sendUdpRunnable)
        Log.d(TAG, "UDP loop started")
    }

    private fun sendUdpMessageForAction(action: String) {
        Log.d(TAG, "Attempting UDP send for action=$action, ip=$ipAddress, port=$port")
        if (ipAddress.isBlank() || port !in 1..65535) {
            Log.w(TAG, "Invalid config: ip=$ipAddress, port=$port")
            return
        }

        Log.d(TAG, "SSID used: $hardcodedSsid")
        try {
            val connectivityManager = getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
            val activeNetwork = connectivityManager.activeNetwork
            if (activeNetwork == null) {
                Log.w(TAG, "No network available, skipping UDP")
                return
            }

            val macAddress = try {
                getMACAddress(this, hardcodedSsid) ?: "00:00:00:00:00:00"
            } catch (e: Exception) {
                Log.w(TAG, "Failed to get MAC address: ${e.message}")
                "00:00:00:00:00:00"
            }
            val message = "[$macAddress] $action"
            sendUdpMessage(message, ipAddress, port)
            Log.d(TAG, "UDP message sent: $message")
        } catch (e: Exception) {
            Log.e(TAG, "UDP send error: ${e.message}")
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "Service started with intent: $intent")
        Log.d(TAG, "Configuration: SSID=$hardcodedSsid, IP=$ipAddress, Port=$port")

        // Send initial UDP message
        currentAction = "On"
        sendUdpMessageForAction(currentAction)

        return START_STICKY
    }

    private fun createNotificationChannel() {
        try {
            val serviceChannel = NotificationChannel(
                channelId,
                "Screen Service Channel",
                NotificationManager.IMPORTANCE_DEFAULT
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(serviceChannel)
            Log.d(TAG, "Notification channel created")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to create notification channel: ${e.message}")
        }
    }

    private fun createNotification(): Notification {
        try {
            return NotificationCompat.Builder(this, channelId)
                .setContentTitle("Network Monitor Service")
                .setContentText("Monitoring screen state (IP: $ipAddress, Port: $port)")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .build()
        } catch (e: Exception) {
            Log.e(TAG, "Failed to create notification: ${e.message}")
            throw e
        }
    }

    override fun onDestroy() {
        isServiceRunning = false
        handler.removeCallbacks(sendUdpRunnable)
        try {
            if (::screenReceiver.isInitialized) {
                unregisterReceiver(screenReceiver)
                Log.d(TAG, "Screen receiver unregistered")
            } else {
                Log.w(TAG, "Screen receiver not initialized, skipping unregistration")
            }
        } catch (e: Exception) {
            Log.w(TAG, "Error unregistering receiver: ${e.message}")
        }
        Log.d(TAG, "Service destroyed")

        try {
            val workRequest = OneTimeWorkRequestBuilder<StartServiceWorker>().build()
            WorkManager.getInstance(applicationContext).enqueueUniqueWork(
                "startExperimentService",
                ExistingWorkPolicy.REPLACE,
                workRequest
            )
            Log.d(TAG, "Enqueued WorkManager for service restart")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to enqueue WorkManager: ${e.message}")
        }

        super.onDestroy()
    }
    override fun onBind(intent: Intent?): IBinder? = null

    companion object {
        private const val TAG = "ExperimentService"
        private var isServiceRunning = false
        private const val FOREGROUND_SERVICE_TYPE_DATA_SYNC = 0x40000000 // API 34+ constant
    }
}