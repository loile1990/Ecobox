package fr.lip.hownet.networkmonitor.services

import android.content.Context
import android.content.Intent
import android.os.SystemClock
import androidx.work.Worker
import androidx.work.WorkerParameters
import android.util.Log

class StartServiceWorker(appContext: Context, workerParams: WorkerParameters) :
    Worker(appContext, workerParams) {

    override fun doWork(): Result {
        Log.d("StartServiceWorker", "Worker running...")

        val serviceIntent = Intent(applicationContext, ExperimentService::class.java)
        try {
            Log.d("StartServiceWorker", "Starting ExperimentService")
            applicationContext.startForegroundService(serviceIntent)
        } catch (e: Exception) {
            Log.e("StartServiceWorker", "Failed to start foreground service", e)
            return Result.failure()
        }

        return Result.success()
    }
}
