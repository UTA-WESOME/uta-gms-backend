param (
    [string]$environment
)

# Check if the environment parameter is empty
if ([string]::IsNullOrWhiteSpace($environment)) {
    Write-Host "Please specify an environment: dev or dev-custom-engine"
} else {
    # Define the base Docker directory
    $dockerBaseDir = ".\docker\"

    # Determine the Docker Compose file based on the environment parameter
    if ($environment -eq "dev-custom-engine") {
        $dockerComposeFile = "docker-compose.custom-engine.yml"
    } else {
        $dockerComposeFile = "docker-compose.yml"
    }

    # Check if the specified environment directory exists
    $dockerDir = Join-Path -Path $dockerBaseDir -ChildPath $environment
    if (Test-Path -Path $dockerDir -PathType Container) {
        # Store the current directory in a variable
        $currentDir = Get-Location
        try {
            # Change to the specified directory
            Set-Location -Path $dockerDir

            # Skip the first argument (environment) and store the rest in $arguments
            $arguments = $args[1..($args.Length - 1)]

            # Run Docker Compose with the appropriate file and additional parameters
            Write-Host "--------------------------------------------------"
            Write-Host "Running Docker Compose with the following command:"
            Write-Host "docker compose -f $dockerComposeFile $($arguments -join ' ')"
            Write-Host "--------------------------------------------------"
            & "docker" "compose" "-f" $dockerComposeFile $($arguments -join ' ')
        } finally {
            # Restore the original directory
            Set-Location -Path $currentDir
        }
    } else {
        Write-Host "Usage: .\run.ps1 <environment>"
        Write-Host "  Available environments: dev, dev-custom-engine"
        Write-Host "  Example: .\run.ps1 dev"
    }
}
