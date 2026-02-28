package fr.lip.hownet.networkmonitor.services

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import androidx.work.WorkManager
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED || intent.action == Intent.ACTION_MY_PACKAGE_REPLACED) {
            val workRequest = OneTimeWorkRequestBuilder<StartServiceWorker>().build()

            WorkManager.getInstance(context).enqueueUniqueWork(
                "startExperimentService",
                ExistingWorkPolicy.REPLACE,
                workRequest
            )
            Log.d("BootReceiver", "WorkManager enqueued StartServiceWorker")
        }
    }
}